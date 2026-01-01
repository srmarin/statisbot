from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_groq import ChatGroq
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"
client = Groq(api_key=GROQ_API_KEY)


def summary_chain(chat_history):

    system_template = """You are a telegram bot assistant that specializes in summarizing chat messages that user sends you. 
    You must sound familiar. The text has 100 words max.
    Maybe the messages are responses to another messages or a new message starts a new thread. 
    Answer only with the summary translated into Spanish."""
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

    human_message_prompt = HumanMessagePromptTemplate.from_template("{chat_history}")
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    request = chat_prompt.format_prompt(chat_history=chat_history).to_messages()

    chat = ChatGroq(model_name=MODEL, temperature=0.2, groq_api_key=GROQ_API_KEY)
    result = chat.invoke(request)
    return result.content


def speak_as_us(chat_history):

    system_template = """Eres un bot de telegram que se dedica a entender y copiar la forma de hablar de la gente de un grupo.
    Tu trabajo es enviar mensajes de la misma forma que lo haría alguien del grupo dando conversación o respondiendo mensajes.
    Responde siempre en español. La longitud del mensaje no debe ser superior a 200 palabras. El formato es complemtanente informal.
    Evita adjetivos como 'divertida', 'bonita' o 'chula'.
    """
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

    human_message_prompt = HumanMessagePromptTemplate.from_template("{chat_history}")
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    request = chat_prompt.format_prompt(chat_history=chat_history).to_messages()

    chat = ChatGroq(model_name=MODEL, temperature=0.6, groq_api_key=GROQ_API_KEY)
    result = chat.invoke(request)
    return result.content


def speech_to_text(voice_message):
    
    try:
        with open(voice_message, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(voice_message, file.read()),
                model="distil-whisper-large-v3-en",
                response_format="verbose_json",
            )
            return transcription.text
    except FileExistsError as fe:
        print(fe)
        return "No se pudo procesar el mensaje"
    except Exception as ex:
        print(ex)
        return "Hubo un problema"
