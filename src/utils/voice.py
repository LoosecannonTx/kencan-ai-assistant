"""
Voice Module for Kencan
Text-to-Speech and Speech-to-Text capabilities
"""

import logging
from typing import Optional, Callable
import threading
import queue

logger = logging.getLogger(__name__)

# TTS Engine
_tts_engine = None
_tts_queue = queue.Queue()
_tts_thread = None


def _init_tts():
    """Initialize text-to-speech engine"""
    global _tts_engine
    try:
        import pyttsx3
        _tts_engine = pyttsx3.init()
        # Configure voice
        _tts_engine.setProperty('rate', 175)  # Speed
        _tts_engine.setProperty('volume', 0.9)
        
        # Try to use a female voice if available
        voices = _tts_engine.getProperty('voices')
        for voice in voices:
            if 'zira' in voice.name.lower() or 'female' in voice.name.lower():
                _tts_engine.setProperty('voice', voice.id)
                break
        
        logger.info("TTS engine initialized")
        return True
    except ImportError:
        logger.warning("pyttsx3 not installed. Run: pip install pyttsx3")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize TTS: {e}")
        return False


def _tts_worker():
    """Background worker for TTS to avoid blocking"""
    global _tts_engine
    while True:
        text = _tts_queue.get()
        if text is None:  # Shutdown signal
            break
        try:
            if _tts_engine:
                _tts_engine.say(text)
                _tts_engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS error: {e}")
        _tts_queue.task_done()


def speak(text: str, blocking: bool = False):
    """Speak text using TTS"""
    global _tts_thread, _tts_engine
    
    if _tts_engine is None:
        if not _init_tts():
            print(f"[Voice disabled] {text}")
            return
    
    # Start worker thread if not running
    if _tts_thread is None or not _tts_thread.is_alive():
        _tts_thread = threading.Thread(target=_tts_worker, daemon=True)
        _tts_thread.start()
    
    if blocking:
        # Speak directly on main thread
        try:
            _tts_engine.say(text)
            _tts_engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS error: {e}")
    else:
        # Queue for background speaking
        _tts_queue.put(text)


def stop_speaking():
    """Stop current speech"""
    global _tts_engine
    if _tts_engine:
        try:
            _tts_engine.stop()
        except:
            pass


# Speech Recognition
_recognizer = None
_microphone = None


def _init_speech_recognition():
    """Initialize speech recognition"""
    global _recognizer, _microphone
    try:
        import speech_recognition as sr
        _recognizer = sr.Recognizer()
        _microphone = sr.Microphone()
        
        # Adjust for ambient noise
        with _microphone as source:
            _recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        logger.info("Speech recognition initialized")
        return True
    except ImportError:
        logger.warning("speech_recognition not installed. Run: pip install SpeechRecognition pyaudio")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize speech recognition: {e}")
        return False


def listen(timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
    """Listen for speech and return recognized text"""
    global _recognizer, _microphone
    
    if _recognizer is None:
        if not _init_speech_recognition():
            return None
    
    try:
        import speech_recognition as sr
        
        with _microphone as source:
            print("🎤 Listening...")
            audio = _recognizer.listen(
                source, 
                timeout=timeout,
                phrase_time_limit=phrase_time_limit
            )
        
        print("Processing speech...")
        
        # Try Google Speech Recognition (free, no API key needed)
        try:
            text = _recognizer.recognize_google(audio)
            logger.info(f"Recognized: {text}")
            return text
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Listen error: {e}")
        return None


def listen_continuous(callback: Callable[[str], None], 
                      wake_word: str = "kencan",
                      stop_event: threading.Event = None):
    """
    Continuously listen for wake word, then process commands
    
    Args:
        callback: Function to call with recognized text
        wake_word: Word to trigger listening (default: "kencan")
        stop_event: Threading event to stop listening
    """
    global _recognizer, _microphone
    
    if _recognizer is None:
        if not _init_speech_recognition():
            return
    
    import speech_recognition as sr
    
    print(f"🎤 Listening for wake word '{wake_word}'...")
    
    while stop_event is None or not stop_event.is_set():
        try:
            with _microphone as source:
                audio = _recognizer.listen(source, timeout=2, phrase_time_limit=5)
            
            try:
                text = _recognizer.recognize_google(audio).lower()
                
                if wake_word.lower() in text:
                    # Wake word detected, listen for command
                    speak("Yes?", blocking=True)
                    
                    with _microphone as source:
                        print("🎤 Listening for command...")
                        command_audio = _recognizer.listen(
                            source, 
                            timeout=5,
                            phrase_time_limit=15
                        )
                    
                    command = _recognizer.recognize_google(command_audio)
                    logger.info(f"Command: {command}")
                    callback(command)
                    
            except sr.UnknownValueError:
                pass  # Silence or unclear audio
            except sr.RequestError:
                pass  # Service error
                
        except sr.WaitTimeoutError:
            pass  # No speech detected
        except Exception as e:
            logger.error(f"Continuous listen error: {e}")


class VoiceAssistant:
    """Combined voice assistant for Kencan"""
    
    def __init__(self, wake_word: str = "kencan"):
        self.wake_word = wake_word
        self.listening = False
        self._stop_event = threading.Event()
        self._listen_thread = None
        self.command_callback = None
    
    def say(self, text: str, blocking: bool = False):
        """Speak text"""
        speak(text, blocking)
    
    def listen_once(self) -> Optional[str]:
        """Listen for a single command"""
        return listen()
    
    def start_continuous(self, command_callback: Callable[[str], None]):
        """Start continuous listening with wake word"""
        self.command_callback = command_callback
        self._stop_event.clear()
        self._listen_thread = threading.Thread(
            target=listen_continuous,
            args=(command_callback, self.wake_word, self._stop_event),
            daemon=True
        )
        self._listen_thread.start()
        self.listening = True
    
    def stop_continuous(self):
        """Stop continuous listening"""
        self._stop_event.set()
        self.listening = False
        if self._listen_thread:
            self._listen_thread.join(timeout=2)
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_continuous()
        stop_speaking()


# Convenience function for quick voice response
def respond(text: str):
    """Print and speak a response"""
    print(f"🔊 {text}")
    speak(text)
