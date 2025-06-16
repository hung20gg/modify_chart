import streamlit as st
import streamlit.components.v1 as components
import os
import logging
from PIL import Image
import io

from text2chart import Text2Chart, Router
from text2sql.text2sql_agent import SQLAgent
from text2sql.postgres_utils import PostgresDB
from pipeline.module import Module, ModuleConfig
from pipeline.iterative import IterativePipeline
from agent import (
    ActorConfig,
    CriticConfig,
    TextCriticConfig,
    VisionCriticConfig
)
from pipeline.execution import PythonEnv, PythonEnvConfig, HtmlEnv, HtmlEnvConfig
from utils import open_image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Streamlit UI ---
st.set_page_config(page_title="Interactive Chart Generator & Editor", layout="wide")
st.title("Interactive Chart Generator & Editor")

# Initialize session state
if "text2chart" not in st.session_state:
    st.session_state.text2chart = None
    st.session_state.current_image = None
    st.session_state.image_history = []
    st.session_state.code_history = []
    st.session_state.messages = []

# Sidebar for configuration
st.sidebar.header("Configuration")

# Language selection
language_type = st.sidebar.selectbox("Select Language Type", ["python", "html"], index=0)

# Model selection
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
vision_model = st.sidebar.selectbox("Vision Model", model_choices, index=0)
code_model = st.sidebar.selectbox("Code Generation Model", model_choices, index=0)

# Additional settings
max_iterations = st.sidebar.slider("Max Iterations", 1, 10, 3)
debug = st.sidebar.checkbox("Debug Mode", value=False)
think_mode = st.sidebar.checkbox("Think Mode", value=False, help="Enable iterative thinking mode")


def initialize_text2chart():
    """Initialize the Text2Chart object with all components"""
    # For router and SQL, always use gpt-4.1-mini as specified
    router_model = "gpt-4.1-mini"
    sql_model = "gpt-4.1-mini"
    
    # Set up environment based on language choice
    if language_type == "python":
        actor_config = ActorConfig(name="Actor", model_name=code_model, code='python', debug=debug)
        vision_critic_config = VisionCriticConfig(name="Vision Critic", model_name=vision_model, debug=debug)
        text_critic_config = TextCriticConfig(name="Text Critic", model_name=vision_model, code='python', debug=debug)
        critic_config = CriticConfig(name="Critic", vision=vision_critic_config, text=text_critic_config, model_name=code_model)
        module_config = ModuleConfig(name="Module", actor_config=actor_config, critic_config=critic_config, code='python', debug=debug)
        module = Module(config=module_config)
        env = PythonEnv(config=PythonEnvConfig(name="Python Environment"))
    else:
        actor_config = ActorConfig(name="Actor", model_name=code_model, code='html', debug=debug)
        vision_critic_config = VisionCriticConfig(name="Vision Critic", model_name=vision_model, debug=debug)
        text_critic_config = TextCriticConfig(name="Text Critic", model_name=vision_model, code='html', debug=debug)
        critic_config = CriticConfig(name="Critic", vision=vision_critic_config, text=text_critic_config, model_name=code_model)
        module_config = ModuleConfig(name="Module", actor_config=actor_config, critic_config=critic_config, code='html', debug=debug)
        module = Module(config=module_config)
        env = HtmlEnv(config=HtmlEnvConfig(name="HTML Environment"))

    iterative_pipeline = IterativePipeline(module=module, env=env, max_iterations=max_iterations, debug=debug)
    router = Router(model_name=router_model)
    
    # Database connection
    try:
        db = PostgresDB(host='localhost', database='postgres', user='postgres', password='12345678', port='5432')
        sql_agent = SQLAgent(db=db, model_name=sql_model)
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        sql_agent = None
    
    return Text2Chart(
        router=router,
        sql_agent=sql_agent,
        iterative_pipeline=iterative_pipeline,
        actor=module.actor,
        env=env,
        debug=debug
    )

# Button to clear state and start fresh
if st.sidebar.button("Clear State"):
    st.session_state.text2chart = None
    st.session_state.current_image = None
    st.session_state.image_history = []
    st.session_state.code_history = []
    st.session_state.messages = []
    st.success("State cleared! Ready for a new chart.")

# Initialize Text2Chart if needed
if st.session_state.text2chart is None:
    with st.spinner("Initializing chart generator..."):
        st.session_state.text2chart = initialize_text2chart()

# Display current image if available
if st.session_state.current_image:
    st.subheader("Current Chart")
    st.image(st.session_state.current_image, use_container_width=True)

# User input section
st.header("Chart Request")
user_request = st.text_area("Enter your request to create or modify the chart:")
input_image = st.file_uploader("Upload an input image (optional)", type=["png", "jpg", "jpeg"])

# Process the request
if st.button("Generate/Modify Chart"):
    if not user_request.strip():
        st.warning("Please enter a request.")
    else:
        # Process uploaded image if provided
        image = None
        if input_image is not None:
            image = Image.open(input_image)
        
        # Use current image as context if available and no new image provided
        elif st.session_state.current_image and not input_image:
            image = st.session_state.current_image
        
        with st.spinner("Processing your request..."):
            progress_placeholder = st.empty()
            code_placeholder = st.empty()
            result_placeholder = st.empty()
            
            try:
                process_method = st.session_state.text2chart.process_request if think_mode else st.session_state.text2chart.process_request_single
                
                for step in process_method(user_request, image):
                    current_iteration = step.get('iteration', 0)
                    progress_placeholder.text(f"Status: {step.get('status', 'Processing')} - {step.get('message', '')}")
                    
                    # Handle different response types
                    if step.get('type') == 'code':
                        with code_placeholder.expander("Generated Code", expanded=False):
                            st.code(step.get('code', ''), language=step.get('language', 'python'))
                        language = step.get('language', 'python')
                        # Store code in history
                        st.session_state.code_history.append({
                            'code': step.get('code', ''),
                            'language': language,
                            'timestamp': st.session_state.messages[-1]['timestamp'] if st.session_state.messages else None
                        })

                        
                        
                        # Display resulting image if available
                        if 'image_file_path' in step and step['image_file_path']:
                            output_image = open_image(step['image_file_path'])
                            st.session_state.current_image = output_image
                            st.session_state.image_history.append(output_image)
                            # result_placeholder.image(output_image, use_container_width=True)

                        if language == 'python':
                            image = step.get('image_file_path', None)
                            if image:
                                if isinstance(image, str) and os.path.exists(image):
                                    image = open_image(image)
                                # with cols[idx]:
                                st.image(image, caption=f"Iteration {current_iteration}", use_container_width=True)
                                with st.expander(f"Python Code - Iteration {current_iteration}", expanded=False):
                                    st.code(step.get('code', ''), language='python')

                        elif language == 'html':
                            html_content = step.get('code', None)
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
                                components.html(responsive_html, height=600, scrolling=True)  
                                with st.expander(f"HTML Code - Iteration {current_iteration}", expanded=False):
                                    st.code(html_content, language='html')
                                
                                st.write(f"Iteration {current_iteration} HTML content displayed.")
                    
                    elif step.get('type') == 'table':
                        with result_placeholder.expander("SQL Query Result", expanded=True):
                            st.markdown(step.get('content', 'No data available'))
                
                # Add message to history
                import datetime
                st.session_state.messages.append({
                    'request': user_request,
                    'timestamp': datetime.datetime.now(),
                })
                
                progress_placeholder.success("Processing complete!")
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.exception("Error processing request")

# History section
if st.session_state.messages:
    with st.expander("Request History", expanded=False):
        for i, msg in enumerate(st.session_state.messages):
            st.markdown(f"**Request {i+1}**: {msg['request']} ({msg['timestamp'].strftime('%Y-%m-%d %H:%M:%S')})")
            
            # Find associated code if available
            for code_entry in st.session_state.code_history:
                if code_entry['timestamp'] == msg['timestamp']:
                    st.code(code_entry['code'], language=code_entry['language'])
                    break

# Footer
st.markdown("---")
st.markdown("Designed for interactive chart generation and modification. Use 'Clear State' to reset.")