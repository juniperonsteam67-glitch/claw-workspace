# Free/Open-Source TTS Alternatives to ElevenLabs

*Research conducted: 2026-02-09*

This document evaluates free and open-source text-to-speech (TTS) options for Linux, with a focus on voice quality, ease of installation, latency, and Python API availability.

---

## Executive Summary / Recommendation

**🏆 Top Recommendation: Piper TTS**

For most use cases, **Piper TTS** is the clear winner. It offers:
- Excellent voice quality (neural, natural-sounding)
- Fast real-time synthesis (even on Raspberry Pi)
- Simple pip installation
- Native Python API
- Low latency (<200ms on decent hardware)
- Active maintenance by Open Home Foundation

**Runner-up: Coqui TTS** for advanced features like voice cloning, or **eSpeak-NG** for maximum speed with acceptable quality loss.

---

## Detailed Evaluation

### 1. Piper TTS ⭐ (RECOMMENDED)

| Aspect | Rating | Details |
|--------|--------|---------|
| **Voice Quality** | ⭐⭐⭐⭐⭐ | Neural synthesis, natural-sounding, multiple quality levels (low/medium/high) |
| **Installation** | ⭐⭐⭐⭐⭐ | `pip install piper-tts` - pre-built wheels available |
| **Latency** | ⭐⭐⭐⭐⭐ | Real-time synthesis; RTF < 0.1 on modern CPUs |
| **Python API** | ⭐⭐⭐⭐⭐ | Native, well-documented, streaming support |
| **License** | MIT | Free for commercial use |

**Key Features:**
- **30+ languages** supported with 100+ voices
- ONNX Runtime for efficient inference
- GPU acceleration available (CUDA)
- Voice quality levels: x_low, low, medium, high
- Streaming synthesis for real-time applications
- Used by Home Assistant, NVDA, Open Voice OS

**Installation:**
```bash
# System dependencies (Ubuntu/Debian)
sudo apt-get install libespeak-ng1

# Python package
pip install piper-tts

# Download a voice
python3 -m piper.download_voices en_US-lessac-medium
```

**Python API Example:**
```python
import wave
from piper import PiperVoice

voice = PiperVoice.load("/path/to/en_US-lessac-medium.onnx")

# Basic synthesis
with wave.open("output.wav", "wb") as wav_file:
    voice.synthesize_wav("Hello world!", wav_file)

# With configuration
from piper import SynthesisConfig
config = SynthesisConfig(
    volume=0.9,
    length_scale=1.0,  # speed
    noise_scale=0.667,  # variation
)
voice.synthesize_wav("Hello!", wav_file, syn_config=config)

# Streaming (for real-time)
for chunk in voice.synthesize("Hello world!"):
    play_audio(chunk.audio_int16_bytes)

# GPU acceleration
voice = PiperVoice.load("voice.onnx", use_cuda=True)
```

**Current Status:** 
- Original repo (rhasspy/piper) archived in Oct 2025
- **Active development at:** https://github.com/OHF-Voice/piper1-gpl
- Open Home Foundation is seeking maintainers

---

### 2. Coqui TTS (Idiap Fork)

| Aspect | Rating | Details |
|--------|--------|---------|
| **Voice Quality** | ⭐⭐⭐⭐⭐ | State-of-the-art; XTTS v2 for voice cloning |
| **Installation** | ⭐⭐⭐ | Requires PyTorch; more complex dependencies |
| **Latency** | ⭐⭐⭐ | Slower than Piper; XTTS <200ms possible |
| **Python API** | ⭐⭐⭐⭐⭐ | Excellent, feature-rich |
| **License** | MPL-2.0 | Open source |

**Key Features:**
- **1100+ languages** via Fairseq models
- Voice cloning (XTTS v2) - clone from 6-second sample
- Multiple architectures: Tacotron2, VITS, Bark, Tortoise
- Voice conversion models (FreeVC, kNN-VC, OpenVoice)
- Well-documented, research-grade

**Installation:**
```bash
# Requires Python 3.10-3.14
pip install torch torchaudio  # Install PyTorch first
pip install coqui-tts

# For GPU
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Python API Example:**
```python
import torch
from TTS.api import TTS

device = "cuda" if torch.cuda.is_available() else "cpu"

# Basic TTS
tts = TTS("tts_models/en/ljspeech/tacotron2-DDC").to(device)
tts.tts_to_file(text="Hello world!", file_path="output.wav")

# XTTS - Voice cloning with 6-second sample
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
tts.tts_to_file(
    text="This is a cloned voice!",
    speaker_wav="sample_audio.wav",
    language="en",
    file_path="output.wav"
)
```

**Trade-offs:**
- Heavier resource usage than Piper
- Larger model downloads (hundreds of MB to GB)
- More complex setup with PyTorch dependencies

**Current Status:**
- Original Coqui shut down in 2024
- **Actively maintained fork:** https://github.com/idiap/coqui-ai-TTS
- New PyPI package: `coqui-tts`

---

### 3. eSpeak-NG

| Aspect | Rating | Details |
|--------|--------|---------|
| **Voice Quality** | ⭐⭐ | Robotic, formant-based synthesis |
| **Installation** | ⭐⭐⭐⭐⭐ | In most distro repos; tiny footprint |
| **Latency** | ⭐⭐⭐⭐⭐ | Extremely fast - realtime on any hardware |
| **Python API** | ⭐⭐⭐ | Via `pyttsx3` or `espeakng` bindings |
| **License** | GPL-3.0+ | Open source |

**Key Features:**
- **100+ languages and accents**
- Ultra-compact (~10MB total)
- Command-line and library interfaces
- SSML support
- Can front-end for MBROLA voices (better quality)
- Works at very high speeds

**Installation:**
```bash
# Ubuntu/Debian
sudo apt-get install espeak-ng

# Python bindings
pip install espeakng
```

**Usage:**
```bash
# Command line
espeak-ng "Hello world"
espeak-ng -w output.wav "Hello world"

# With mbrola for better quality
espeak-ng -v mb/mb-us1 "Hello world"
```

**When to Use:**
- Maximum speed is critical
- Resource-constrained environments
- Screen readers and accessibility tools
- Acceptable quality loss for latency

---

### 4. Mimic 3 (DEPRECATED)

| Aspect | Rating | Details |
|--------|--------|---------|
| **Status** | ❌ | No longer maintained |
| **Successor** | → | Use **Piper TTS** instead |

Mimic 3 was developed by Mycroft for the Mark II device. The developers explicitly recommend **Piper TTS** as the spiritual successor.

---

### 5. Larynx (DEPRECATED)

| Aspect | Rating | Details |
|--------|--------|---------|
| **Status** | ❌ | No longer maintained |
| **Successor** | → | Use **Piper TTS** instead |

Larynx used GlowTTS + HiFi-GAN. Development ceased in favor of Piper.

---

### 6. Bark (by Suno)

| Aspect | Rating | Details |
|--------|--------|---------|
| **Voice Quality** | ⭐⭐⭐⭐⭐ | Highly realistic, emotional, can laugh/sigh/cry |
| **Installation** | ⭐⭐⭐ | Heavy dependencies; ~12GB VRAM recommended |
| **Latency** | ⭐⭐ | Slow; not real-time on consumer hardware |
| **Python API** | ⭐⭐⭐⭐ | Good, but resource-intensive |
| **License** | MIT | Open source |

**Key Features:**
- Generative audio model (not traditional TTS)
- Multilingual (13 languages)
- Non-speech sounds (laughter, sighs, music)
- ~13 second maximum per generation
- Creative/storytelling applications

**When to Use:**
- Creative content where quality > speed
- Non-standard speech (singing, emotions)
- High-end GPU available (12GB+ VRAM)

**When NOT to Use:**
- Real-time applications
- Resource-constrained environments
- Simple voice announcements

---

### 7. Festival Speech Synthesis System

| Aspect | Rating | Details |
|--------|--------|---------|
| **Voice Quality** | ⭐⭐ | Older diphone synthesis; acceptable but dated |
| **Installation** | ⭐⭐ | Available in repos; multiple packages needed |
| **Latency** | ⭐⭐⭐⭐ | Fast enough for most uses |
| **Python API** | ⭐⭐ | Via subprocess or `pyfestival` bindings |
| **License** | X11-style | Permissive, commercial-friendly |

**Key Features:**
- Established, mature project from University of Edinburgh
- Multiple APIs: shell, Scheme, C++, Emacs
- US/UK English and Spanish included
- Many community voices available

**Installation:**
```bash
sudo apt-get install festival
```

**When to Use:**
- Legacy system compatibility
- Research/educational purposes
- When you need Scheme scripting

---

### 8. OpenTTS

| Aspect | Rating | Details |
|--------|--------|---------|
| **Purpose** | Unification | HTTP API wrapper for multiple TTS systems |
| **Features** | ⭐⭐⭐⭐ | Supports Piper, Coqui, eSpeak, Festival, etc. |

**Use Case:**
- Provides a unified HTTP API over multiple TTS backends
- MaryTTS-compatible endpoint
- Good for applications that need to support multiple engines

**Docker Run:**
```bash
docker run -it -p 5500:5500 synesthesiam/opentts:en
```

---

## Comparison Matrix

| Engine | Quality | Speed | Install | Python API | GPU | Best For |
|--------|---------|-------|---------|------------|-----|----------|
| **Piper** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Optional | General use, real-time |
| **Coqui** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Recommended | Voice cloning, research |
| **eSpeak-NG** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | No | Speed-critical, embedded |
| **Bark** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Required | Creative content |
| **Festival** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | No | Legacy, research |

---

## Quick Start Guide

### For Most Users (Recommended)
```bash
# 1. Install
pip install piper-tts

# 2. Download voice
python3 -m piper.download_voices en_US-lessac-medium

# 3. Use in Python
python3 -c "
from piper import PiperVoice
import wave
voice = PiperVoice.load('en_US-lessac-medium.onnx')
with wave.open('test.wav', 'wb') as wav_file:
    voice.synthesize_wav('Hello from Piper TTS!', wav_file)
"
```

### For Voice Cloning
```bash
# Install Coqui TTS
pip install torch torchaudio
pip install coqui-tts

# Python code
from TTS.api import TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
tts.tts_to_file(
    text="Cloned voice speaking!",
    speaker_wav="your_sample.wav",
    language="en",
    file_path="output.wav"
)
```

---

## Resources

- **Piper TTS (Active):** https://github.com/OHF-Voice/piper1-gpl
- **Piper Voices:** https://huggingface.co/rhasspy/piper-voices
- **Coqui TTS (Idiap Fork):** https://github.com/idiap/coqui-ai-TTS
- **Piper PyPI:** https://pypi.org/project/piper-tts/
- **Coqui PyPI:** https://pypi.org/project/coqui-tts/

---

## Notes for Implementation

1. **Piper is the drop-in replacement for ElevenLabs** - similar quality, local, free
2. **Start with medium quality voices** - good balance of size/quality
3. **Use ONNX Runtime GPU** if available for even faster synthesis
4. **Coqui XTTS v2** for voice cloning requires ~4GB VRAM minimum
5. **eSpeak-NG** as fallback for maximum compatibility
6. Consider **OpenTTS** if you need to support multiple engines behind one API

---

*Document generated by subagent for TTS research task.*
