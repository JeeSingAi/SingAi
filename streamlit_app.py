import asyncio
import platform
import subprocess
import streamlit as st
import base64
from datetime import datetime
import os
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from openai import OpenAI
import uuid

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
os.environ['PINECONE_API_KEY'] = st.secrets['PINECONE_API_KEY']

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = PineconeVectorStore.from_existing_index(
    index_name="rag-assistant",
    embedding=embeddings
)

st.set_page_config(
    page_title="SingAI Unified Government Chatbot",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'input_key' not in st.session_state:
    st.session_state.input_key = str(uuid.uuid4())
if 'last_user_input_content' not in st.session_state:
    st.session_state.last_user_input_content = ""

logo_base64 = ""
try:
    with open("logo.png", "rb") as img_file:
        logo_base64 = base64.b64encode(img_file.read()).decode()
except FileNotFoundError:
    st.warning("Logo file 'logo.png' not found. Please ensure it's in the same directory.")
except Exception as e:
    st.error(f"An error occurred while loading the logo: {e}")

header_image_base64 = ""
try:
    with open("image_204982.png", "rb") as img_file:
        header_image_base64 = base64.b64encode(img_file.read()).decode()
except FileNotFoundError:
    st.warning("Header image 'image_204982.png' not found. Please ensure it's in the same directory.")
except Exception as e:
    st.error(f"Error loading header image: {e}")

brain_image_base64 = ""
try:
    with open("image_204563.png", "rb") as img_file:
        brain_image_base64 = base64.b64encode(img_file.read()).decode()
except FileNotFoundError:
    st.warning("Brain image 'image_204563.png' not found. Please ensure it's in the same directory.")
except Exception as e:
    st.error(f"Error loading brain image: {e}")

st.markdown(f"""
    <style>
        /* Main app styling with transparent brain image background */
        .stApp {{
            background: linear-gradient(135deg, rgba(26, 43, 43, 0.8) 0%, rgba(42, 64, 48, 0.8) 50%, rgba(26, 53, 53, 0.8) 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            position: relative;
        }}

        .stApp::before {{
            content: "";
            background-image: url('data:image/png;base64,{brain_image_base64}');
            background-repeat: no-repeat;
            background-position: center center;
            background-size: cover;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0.3;
            z-index: -1;
        }}

        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        .chat-container {{
            max-width: 950px;
            margin: auto;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 90%;
            height: 80vh;
            display: flex;
            flex-direction: column;
            background: rgba(26, 43, 43, 0.9);
            border: 2px solid rgba(42, 64, 48, 0.4);
            border-radius: 25px;
            box-shadow: 0 0 50px rgba(42, 64, 48, 0.3),
                        inset 0 0 25px rgba(42, 64, 48, 0.15);
            overflow: hidden;
            backdrop-filter: blur(10px);
        }}

        .chat-header {{
            background: linear-gradient(90deg, rgba(42, 64, 48, 0.4) 0%, rgba(26, 53, 53, 0.4) 100%);
            padding: 25px;
            text-align: center;
            border-bottom: 2px solid rgba(42, 64, 48, 0.5);
            position: relative;
        }}

        .header-image {{
            max-width: 80%;
            height: auto;
            display: block;
            margin: 0 auto;
            filter: drop-shadow(0 0 10px rgba(255, 255, 0, 0.7));
        }}

        /* Messages area */
        .messages-area {{
            flex: 1;
            overflow-y: auto;
            padding: 25px 35px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            background: rgba(26, 43, 43, 0.8);
            min-height: 0;
        }}

        /* Message bubbles */
        .message {{
            max-width: 75%;
            padding: 18px 25px;
            border-radius: 20px;
            position: relative;
            animation: fadeIn 0.6s ease-out;
            font-size: 18px; /* Increased for better readability */
            line-height: 1.8; /* Improved spacing */
            color: #E0E7E9;
        }}

        .user-message {{
            align-self: flex-start;
            background: linear-gradient(135deg, rgba(46, 74, 74, 0.6) 0%, rgba(34, 51, 34, 0.6) 100%);
            border: 1px solid rgba(46, 74, 74, 0.7);
            box-shadow: 0 6px 20px rgba(46, 74, 74, 0.5);
            margin-right: auto;
            margin-left: 0;
        }}

        .bot-message {{
            align-self: flex-end;
            background: linear-gradient(135deg, rgba(64, 96, 64, 0.6) 0%, rgba(46, 74, 74, 0.6) 100%);
            border: 1px solid rgba(64, 96, 64, 0.7);
            box-shadow: 0 6px 20px rgba(64, 96, 64, 0.5);
            margin-left: auto;
            margin-right: 0;
            color: #FFFFFF; /* High contrast text color */
        }}

        .message-time {{
            font-size: 11px;
            color: rgba(255, 255, 255, 0.5);
            margin-top: 10px;
        }}

        .user-message .message-time {{
            text-align: right;
        }}

        .bot-message .message-time {{
            text-align: left;
        }}

        /* Welcome message */
        .welcome-message {{
            text-align: center;
            margin: auto;
            color: #E0E7E9;
            padding: 30px;
        }}

        .welcome-message h2 {{
            font-size: 30px;
            margin-bottom: 15px;
            color: #E0E7E9;
            font-weight: 700;
            letter-spacing: 1.5px;
        }}

        .welcome-message p {{
            font-size: 20px;
            color: #C0C8CA;
            font-weight: 500;
            line-height: 1.7;
        }}

        /* Input area - now a flex container for input and button */
        .input-container {{
            padding: 25px 30px;
            background: rgba(26, 43, 43, 0.95);
            border-top: 2px solid rgba(42, 64, 48, 0.5);
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        /* Target Streamlit's div wrappers for flex behavior */
        .stTextInput {{
            flex-grow: 1;
            min-width: 150px;
        }}

        .stButton {{
            flex-shrink: 0;
        }}

        /* Custom input styling with 3D effect */
        .stTextInput > div > div > input {{
            background: rgba(34, 51, 34, 0.9) !important;
            border: 2px solid rgba(64, 96, 64, 0.6) !important;
            color: #E0E7E9 !important;
            border-radius: 25px !important;
            padding: 18px 25px !important;
            font-size: 17px !important;
            transition: all 0.4s ease !important;
            box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.4),
                        inset -2px -2px 5px rgba(255, 255, 255, 0.1);
            caret-color: white !important;
        }}

        /* Fix for red border and enhanced 3D/glow on focus */
        .stTextInput > div > div > input:focus,
        .stTextInput > div > div > input:focus-visible,
        .stTextInput > div > div > input:active {{
            border-color: rgba(64, 96, 64, 0.9) !important;
            box-shadow: 0 0 30px rgba(255, 255, 255, 0.8),
                        inset 2px 2px 8px rgba(0, 0, 0, 0.6),
                        inset -2px -2px 8px rgba(255, 255, 255, 0.15) !important;
            outline: none !important;
        }}

        .stTextInput > div > div > input::placeholder {{
            color: rgba(255, 255, 255, 0.4) !important;
        }}

        /* Button styling */
        .stButton > button {{
            background: linear-gradient(90deg, #4CAF50 0%, #388E3C 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 25px !important;
            padding: 18px 35px !important;
            font-size: 17px !important;
            font-weight: 700 !important;
            letter-spacing: 1.2px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 5px 25px rgba(50, 150, 50, 0.5) !important;
            cursor: pointer;
        }}

        .stButton > button:hover {{
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 30px rgba(50, 150, 50, 0.7) !important;
            filter: brightness(1.1);
        }}

        /* Scrollbar styling */
        .messages-area::-webkit-scrollbar {{
            width: 12px;
        }}

        .messages-area::-webkit-scrollbar-track {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
        }}

        .messages-area::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, #4CAF50 0%, #388E3C 100%);
            border-radius: 10px;
            border: 2px solid rgba(0,0,0,0.1);
        }}

        /* Animation */
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        /* Logo styling - Fixed at top-left */
        .logo-container {{
            position: fixed;
            top: 25px;
            left: 25px;
            z-index: 1000;
            opacity: 0.95;
        }}

        /* Glow effect for logo */
        .logo-glow {{
            filter: drop-shadow(0 0 20px rgba(64, 96, 64, 0.8));
        }}

        /* Typing indicator for "..." */
        .message.bot-message .typing-dots {{
            display: inline-flex;
            align-items: center;
        }}

        .message.bot-message .typing-dots span {{
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: #C0C8CA;
            border-radius: 50%;
            margin: 0 2px;
            animation: typing 1.4s infinite ease-in-out;
        }}

        .message.bot-message .typing-dots span:nth-child(1) {{
            animation-delay: 0s;
        }}
        .message.bot-message .typing-dots span:nth-child(2) {{
            animation-delay: 0.2s;
        }}
        .message.bot-message .typing-dots span:nth-child(3) {{
            animation-delay: 0.4s;
        }}

        @keyframes typing {{
            0%, 80%, 100% {{
                transform: translateY(0);
                opacity: 0.6;
            }}
            40% {{
                transform: translateY(-5px);
                opacity: 1;
            }}
        }}
    </style>
""", unsafe_allow_html=True)

if logo_base64:
    st.markdown(f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{logo_base64}" width="80" class="logo-glow">
        </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

st.markdown(f"""
    <div class="chat-header">
        {'<img src="data:image/png;base64,' + header_image_base64 + '" class="header-image">' if header_image_base64 else '<h1 class="chat-title">SingAI Unified Government Chatbot</h1><p class="chat-subtitle">CPF • HDB • Singapore Public Policy</p>'}
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="messages-area">', unsafe_allow_html=True)

if not st.session_state.conversation:
    st.markdown("""
        <div class="welcome-message">
            <h2>Welcome to SingAI</h2>
            <p>Ask me anything about CPF, HDB, or public policies</p>
        </div>
    """, unsafe_allow_html=True)
else:
    for message in st.session_state.conversation:
        message_class = "user-message" if message["role"] == "user" else "bot-message"
        st.markdown(f"""
            <div class="message {message_class}">
                <div>{message["content"]}</div>
                <div class="message-time">{message["timestamp"]}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="input-container">', unsafe_allow_html=True)

user_input = st.text_input(
    "Type your message",
    placeholder="Ask about CPF, HDB, or public policies...",
    key=st.session_state.input_key,
    label_visibility="collapsed"
)

send_button = st.button("Send", key="send_button_fixed")

st.markdown('</div>', unsafe_allow_html=True)

if send_button or (user_input and user_input.strip() != "" and user_input != st.session_state.last_user_input_content):
    if user_input.strip() != "":
        timestamp = datetime.now().strftime("%I:%M %p")
        st.session_state.conversation.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })
        st.session_state.conversation.append({
            "role": "bot",
            "content": '<div class="typing-dots"><span></span><span></span><span></span></div>',
            "timestamp": datetime.now().strftime("%I:%M %p")
        })
        st.session_state.input_key = str(uuid.uuid4())
        st.session_state.last_user_input_content = user_input
        st.rerun()

if st.session_state.conversation and st.session_state.conversation[-1]["role"] == "bot" and '<div class="typing-dots">' in st.session_state.conversation[-1]["content"]:
    current_user_question = st.session_state.conversation[-2]["content"] if len(st.session_state.conversation) >= 2 and st.session_state.conversation[-2]["role"] == "user" else "Tell me about Singapore government policies."
    try:
        search_results = vectorstore.similarity_search(current_user_question, k=3)
        context = "\n".join([doc.page_content for doc in search_results])

        system_instruction = """
You are SingAI, a highly intelligent and helpful assistant specializing in Singapore government policies, including CPF, HDB, and other public policies.
Your goal is to provide accurate, concise, and comprehensive answers.

When responding:
- **Prioritize the provided context** if it's relevant to the user's query.
- If the query requires a **factual, concise answer**, provide it directly, including any relevant section numbers, rule numbers, or regulatory references from the context.
- If the query requires an **elaborate discussion**, connect the provided context with other related topics, offering a comprehensive explanation.
- If you **cannot find specific relevant information** in your knowledge base (the context), politely state that you may not have information on that specific topic or suggest the user try rephrasing their question. **Do not make up information.**
- Maintain a polite, professional, and informative tone.
- **Crucially, after providing a comprehensive answer, always say to user whether the user have any queries or not.  For example- "Let me know if you have any other questions! Please dont use the same sentences all the time, paraphrase it.

NOTE: If the user say Hi or Hello, you must greet them warmly and ask how you can assist them today. DOn't say anything about the context, if user say Hi.
NOTE: If the user asks about any calculation, you must try to assume the missing variables and then calculate it accurately. After the answer, you will must say like this- if you provide me these(assumed) variables then I can calculate more accurately.

ADDITIONAL GUIDANCE:
- Use RAG context to extract key variables (e.g., purchase price, mortgage, refunds) and prioritize them over assumptions.
- For calculations, apply logical constraints from context (e.g., sum of deductions ≤ purchase price) and adjust assumed values if they violate these constraints.
- If variables are missing, assume reasonable values within context limits and request user confirmation (e.g., "I assumed X and Y; please provide exact values for precision").
- Detect illogical results (e.g., totals exceeding limits) and explain adjustments, asking for user input to refine the calculation.
- Maintain a professional tone and invite further queries with varied phrasing (e.g., "Feel free to ask more," "Let me know if you need further assistance").

FURTHER REFINEMENT FOR FORMULAS:
- Use the correct formula for calculations based on the context, e.g., for HDB cash proceeds: Cash Proceeds = Selling Price - (Outstanding Mortgage + CPF Refund), ensuring each deduction is applied only once.
- Verify the formula against the problem's logical structure (e.g., deductions should not be duplicated or exceed the original purchase price).
- If the formula appears incorrect or produces illogical results (e.g., negative proceeds, excessive deductions), pause the calculation, explain the issue (e.g., "The formula resulted in X, which seems incorrect given Y. Let’s adjust it."), and propose a corrected approach with user input.
- Ensure all steps in the calculation are clearly outlined and align with regulatory or contextual rules (e.g., HDB MOP, CPF refund limits).

# NEW: When presenting calculations, provide a clear, step-by-step breakdown using simple arithmetic (e.g., 900,000 - (150,000 + 200,000) = 900,000 - 350,000 = 550,000) and avoid complex or incorrect intermediate expressions (e.g., 900,000 - (900,000 - 350,000)).
# NEW: Ensure all numerical values are formatted consistently without extra commas, line breaks, or spacing errors (e.g., use 900000 or 900,000 uniformly, not 900, 000).
# NEW: If the user requests a step-by-step breakdown, list each step on a new line for clarity (e.g., Step 1: Add Outstanding Mortgage and CPF Refund, Step 2: Subtract from Selling Price).
# NEW: Double-check the final answer against the calculated steps to ensure accuracy before presenting it.
        """
        messages_for_llm = [{"role": "system", "content": system_instruction}]
        for msg in st.session_state.conversation[:-1]:
            if '<div class="typing-dots">' not in msg["content"]:
                role = "assistant" if msg["role"] == "bot" else msg["role"]
                messages_for_llm.append({"role": role, "content": msg["content"]})

        final_prompt = f"Context:\n{context}\n\nQuestion:\n{current_user_question}\n\nProvide a response with calculations if needed, ensuring logical consistency."
        messages_for_llm.append({"role": "user", "content": final_prompt})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_for_llm,
            max_tokens=2000,
            temperature=0.5
        )
        answer = response.choices[0].message.content.strip()

    except Exception as e:
        answer = f"An error occurred: {str(e)}. Please try again or rephrase."
        print(f"OpenAI API/Processing Error: {e}")

    if st.session_state.conversation and st.session_state.conversation[-1]["role"] == "bot" and '<div class="typing-dots">' in st.session_state.conversation[-1]["content"]:
        st.session_state.conversation.pop()

    st.session_state.conversation.append({
        "role": "bot",
        "content": answer,
        "timestamp": datetime.now().strftime("%I:%M %p")
    })
    st.rerun()

st.markdown("""
    <script>
        const messagesArea = document.querySelector('.messages-area');
        if (messagesArea) {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }
    </script>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
