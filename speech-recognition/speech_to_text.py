# Speech to text sdk
import logging
import os

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from promptflow.core import (AzureOpenAIModelConfiguration,
                             OpenAIModelConfiguration, Prompty)

# Load environment variables
load_dotenv()
# Change to logging.DEBUG for more verbose logging from Azure and OpenAI SDKs
logging.basicConfig(level=logging.WARNING)

if not os.getenv("OPENAI_HOST"):
    os.environ["OPENAI_HOST"] = "azure"

def speech_to_text():
    #for this example we will use a pre-recorded audio file so we set 
    #use_default_microphone to False
    use_default_microphone = False
    filename = "../ticket-processing/data/audio-data/issue1.wav"

    speech_config = speechsdk.SpeechConfig(
        subscription=os.environ["SPEECH_KEY"], 
        region=os.environ["SPEECH_REGION"])
    speech_config.speech_recognition_language="en-US"

    if use_default_microphone:
        logging.info("Using the default microphone.")
        audio_config = speechsdk.audio.AudioConfig(
            use_default_microphone=use_default_microphone)
        logging.info("Speak into your microphone.")
    else:
        logging.info(f"Using the audio file: {filename}")
        audio_config = speechsdk.audio.AudioConfig(filename=filename)

        
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_config)
    speech_recognition_result = speech_recognizer.recognize_once_async().get()


    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Speech to text succesful!")
        print('')
        print(f'Full report: {speech_recognition_result.text}')
        print('')
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        logging.warning(
            f'''
            No speech could be recognized: 
            {speech_recognition_result.no_match_details}
            ''')
        logging.warning("No speech could be recognized.")
        exit(1)
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        logging.warning(f"Speech Recognition canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            logging.warning(f"Error details: {cancellation_details.error_details}")
            logging.warning("Did you set the speech resource key and region values?")
            logging.warning(
                f"Speech Recognition canceled: {cancellation_details.reason}")
        exit(1)

    ticket_text = speech_recognition_result.text
    return ticket_text

def text_to_summary(ticket_text):
    # Load prompty with AzureOpenAIModelConfiguration override
    if os.getenv("OPENAI_HOST") == 'azure':
        configuration = AzureOpenAIModelConfiguration(
            azure_deployment=os.environ["AZURE_DEPLOYMENT_NAME"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
        )
        override_model = {
            "configuration": configuration,
            "parameters": {"max_tokens": 512}
        }
 
    elif os.getenv("OPENAI_HOST") == 'openai':
        configuration = OpenAIModelConfiguration(
            model="gpt-35-turbo",
            base_url=os.environ["OPENAI_BASE_URL"],
            api_key=os.environ["OPENAI_API_KEY"],
        )
        override_model = {
            "configuration": configuration,
            "parameters": {"max_tokens": 512}
        }

    prompty_obj = Prompty.load(
        "../ticket-processing/summarize.prompty", model=override_model)
    summary = prompty_obj(problem=ticket_text)

    return summary

reported_issue = speech_to_text()
result = text_to_summary(reported_issue)
print(result)