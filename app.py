import streamlit as st
import os
from PIL import Image
# from pipeline.module import Module, ModuleConfig
# from pipeline.iterative import IterativePipeline
# from agent import (
#     ActorConfig,
#     CriticConfig,
#     TextCriticConfig,
#     VisionCriticConfig
# )
# from pipeline.execution import HtmlEnv, HtmlEnvConfig, PythonEnv, PythonEnvConfig

# --- Streamlit UI ---
st.set_page_config(page_title="Iterative Chart Generator", layout="wide")
st.title("Iterative Chart Generator")

# Sidebar for config
st.sidebar.header("Configuration")
st.session_state.model_type = st.sidebar.selectbox("Select Languge Type", ["python", "html"], index=0)


# User input
st.header("Input")
user_request = st.text_area("Enter your chart request:")
input_image = st.file_uploader("Upload an input image (optional)", type=["png", "jpg", "jpeg"])

max_iterations = st.sidebar.slider("Max Iterations", 1, 10, 5)
debug = st.sidebar.checkbox("Debug Mode", value=False)

# if st.button("Generate Charts"):
#     # Save uploaded image if provided
#     image_path = None
#     if input_image is not None:
#         image_path = os.path.join(".cache", input_image.name)
#         os.makedirs(".cache", exist_ok=True)
#         with open(image_path, "wb") as f:
#             f.write(input_image.read())

#     # Build configs
#     if st.session_state.model_type  == "python":
#         actor_config = ActorConfig(name="Actor", model_name="gpt-4.1-mini", code='python')
#         vision_critic_config = VisionCriticConfig(name="Vision Critic", model_name="gpt-4o")
#         text_critic_config = TextCriticConfig(name="Text Critic", model_name="gpt-4o", code='python')
#         critic_config = CriticConfig(name="Critic", vision=vision_critic_config, text=text_critic_config, model_name="gpt-4.1-mini")
#         module_config = ModuleConfig(name="Module", actor_config=actor_config, critic_config=critic_config)
#         module = Module(config=module_config)
#         env = PythonEnv(config=PythonEnvConfig(name="Python Environment"))
#     else:
#         actor_config = ActorConfig(name="Actor", model_name="gpt-4.1-mini", code='html')
#         vision_critic_config = VisionCriticConfig(name="Vision Critic", model_name="gpt-4o")
#         text_critic_config = TextCriticConfig(name="Text Critic", model_name="gpt-4o", code='html')
#         critic_config = CriticConfig(name="Critic", vision=vision_critic_config, text=text_critic_config, model_name="gpt-4.1-mini")
#         module_config = ModuleConfig(name="Module", actor_config=actor_config, critic_config=critic_config)
#         module = Module(config=module_config)
#         env = HtmlEnv(config=HtmlEnvConfig(name="HTML Environment"))

#     pipeline = IterativePipeline(module=module, env=env, max_iterations=max_iterations, debug=debug)

#     # Run pipeline
#     image_generator = pipeline.stream_act(request=user_request, image=image_path)

#     st.header("Generated Chart Options")
#     images = []
#     cols = st.columns(max_iterations)
#     for idx, chunk in enumerate(image_generator):
#         if idx >= max_iterations:
#             st.warning("Maximum iterations reached.")
#             break
        
#         language = chunk.get('language', 'python')
#         if language != st.session_state.model_type:
#             st.warning(f"Skipping iteration {idx+1} due to language mismatch: {language} != {st.session_state.model_type}")
        
#         if language == 'python':
#             with cols[idx]:
#                 st.image(Image.open(chunk['image_file_path']), caption=f"Iteration {idx+1}", use_column_width=True)

#         elif language == 'html':
#             html_content = chunk.get('html_code', '')
#             with cols[idx]:
#                 st.markdown(html_content, unsafe_allow_html=True)
#                 st.write(f"Iteration {idx+1} HTML content displayed.")
            
        

    

st.markdown("---")
st.markdown("Developed for iterative chart generation and selection.")
