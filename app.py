import streamlit as st
import streamlit.components.v1 as components

import os
from PIL import Image
from pipeline.module import Module, ModuleConfig
from pipeline.iterative import IterativePipeline
from agent import (
    ActorConfig,
    CriticConfig,
    TextCriticConfig,
    VisionCriticConfig
)
from pipeline.execution import HtmlEnv, HtmlEnvConfig, PythonEnv, PythonEnvConfig

# --- Streamlit UI ---
st.set_page_config(page_title="Iterative Chart Generator", layout="wide")
st.title("Iterative Chart Generator")

# Sidebar for config
st.sidebar.header("Configuration")
st.session_state.model_type = st.sidebar.selectbox("Select Languge Type", ["python", "html"], index=0)

model_choices = [
    "gpt-4o", 
    "gpt-4.1-mini", 
    "gpt-4.1", 
    "gemini-2.0-flash", 
    'nim:meta/llama-4-maverick-17b-128e-instruct', 
    'nim:meta/llama-3.2-11b-vision-instruct',
    'nim:meta/llama-3.2-90b-vision-instruct',
    'nim:google/gemma-3-27b-it',
    'google:gemma-3-27b-it'
]

st.sidebar.header("Model Configuration")
vision_model = st.sidebar.selectbox(
    "Vision Model", 
    model_choices,
    index=0
)
code_model = st.sidebar.selectbox(
    "Code Generation Model", 
    model_choices,
    index=0
)

# User input
st.header("Input")
user_request = st.text_area("Enter your chart request:")
input_image = st.file_uploader("Upload an input image (optional)", type=["png", "jpg", "jpeg"])

max_iterations = st.sidebar.slider("Max Iterations", 1, 10, 5)
debug = st.sidebar.checkbox("Debug Mode", value=False)

if st.button("Generate Charts"):
    # Save uploaded image if provided
    image_path = None
    if input_image is not None:
        image_path = os.path.join(".cache", input_image.name)
        os.makedirs(".cache", exist_ok=True)
        with open(image_path, "wb") as f:
            f.write(input_image.read())

    # Build configs
    if st.session_state.model_type == "python":
        actor_config = ActorConfig(name="Actor", model_name=code_model, code='python')
        vision_critic_config = VisionCriticConfig(name="Vision Critic", model_name=vision_model)
        text_critic_config = TextCriticConfig(name="Text Critic", model_name=vision_model, code='python')
        critic_config = CriticConfig(name="Critic", vision=vision_critic_config, text=text_critic_config, model_name=code_model)
        module_config = ModuleConfig(name="Module", actor_config=actor_config, critic_config=critic_config)
        module = Module(config=module_config)
        env = PythonEnv(config=PythonEnvConfig(name="Python Environment"))
    else:
        actor_config = ActorConfig(name="Actor", model_name=code_model, code='html')
        vision_critic_config = VisionCriticConfig(name="Vision Critic", model_name=vision_model)
        text_critic_config = TextCriticConfig(name="Text Critic", model_name=vision_model, code='html')
        critic_config = CriticConfig(name="Critic", vision=vision_critic_config, text=text_critic_config, model_name=code_model)
        module_config = ModuleConfig(name="Module", actor_config=actor_config, critic_config=critic_config)
        module = Module(config=module_config)
        env = HtmlEnv(config=HtmlEnvConfig(name="HTML Environment"))

    pipeline = IterativePipeline(module=module, env=env, max_iterations=max_iterations, debug=debug)

    # Run pipeline
    image_generator = pipeline.stream_act(request=user_request, image=image_path)

    st.header("Generated Chart Options")
    images = []
    cols = st.columns(max_iterations)

    log_container = st.container()
    with log_container:
        st.subheader("Execution Logs")
        logs_placeholder = st.empty()
        all_logs = []

    current_iteration = 0

    for idx, chunk in enumerate(image_generator):
        if current_iteration >= max_iterations:
            st.warning("Maximum iterations reached.")
            break

        current_iteration = chunk.get('iteration', idx + 1)
        
        all_logs.append(f"Iteration {current_iteration} {chunk.get('status', 'unknown')}")
        logs_placeholder.markdown("\n\n".join(all_logs))

        if chunk.get('status') == 'finished':
            continue

        if chunk.get('status') == 'score':
            st.markdown(f"Iteration {current_iteration} scored: {chunk.get('score', 'N/A')}")
            continue
        
        language = chunk.get('language', 'python')
        if language != st.session_state.model_type:
            st.warning(f"Skipping iteration {idx+1} due to language mismatch: {language} != {st.session_state.model_type}")
        
        if language == 'python':
            image = chunk.get('image_file_path', None)
            if image:
                # with cols[idx]:
                st.image(Image.open(chunk['image_file_path']), caption=f"Iteration {current_iteration}", use_container_width=True)
                with st.expander(f"Python Code - Iteration {current_iteration}", expanded=False):
                    st.code(chunk.get('code', ''), language='python')

        elif language == 'html':
            html_content = chunk.get('code', None)
            if html_content:
                # with cols[idx]:
                
                
                # Add responsive wrapper to the HTML content
                responsive_html = f"""
                <div style="width:100%; height:0; padding-bottom:56.25%; position:relative;">
                    <div style="position:absolute; top:0; left:0; width:100%; height:100%;">
                        {html_content}
                    </div>
                </div>
                """
                
                # Display the HTML with responsive container
                components.html(responsive_html, height=600, scrolling=True)  
                with st.expander(f"HTML Code - Iteration {current_iteration}", expanded=False):
                    st.code(html_content, language='html')
                
                st.write(f"Iteration {current_iteration} HTML content displayed.")
                
            
        

    

st.markdown("---")
st.markdown("Developed for iterative chart generation and selection.")
