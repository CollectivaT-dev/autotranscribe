# AutoTranscribe
Automatic transcription with punctuation

### Requisites

- Python modules:
	- vosk-api
	- httpx
- ffmpeg
- PunkProse API token (optional)

### Installation

```
git clone https://github.com/CollectivaT-dev/autotranscribe.git
cd autotranscribe
pip install -r requirements.txt
```

### Usage

Determine the language code:
- `ca`: Catalan
- `es`: Spanish
- `en`: English
- `tr`: Turkish

Simple run:
```
python autotranscribe.py -i <audio_path> -l <lang-code>
```

With punctuation:
```
python autotranscribe.py -i <audio_path> -l <lang-code> -t <punkprose_token>
```

Custom model path:
```
python autotranscribe.py -i <audio_path> -m <model_path>
```

Specify output path:
```
python autotranscribe.py -i <audio_path> -m <model_path> -o <output_path>
```

Usage:
```
python autotranscribe.py -h
```

### Sample run

```
python autotranscribe.py -i sample/hello.wav -l en 
```

### Post-editing on oTranscribe

Automatic speech recognition (ASR) makes errors. If you want to do post-editing on the output, go to [otranscribe.com](https://otranscribe.com/), load your audio file and then import one of the template files with the extension `.otr`. 
