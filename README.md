# AutoTranscribe
Automatic transcription with punctuation

### Requisites

- Python modules:
	- vosk-api
	- httpx
- ffmpeg
- PunkProse API token (optional)

To install:

```
pip install -r requirements.txt
```

### Usage

Determine the language code:
- `ca`: Catalan
- `es`: Spanish
- `en`: English
- `tr`: Turkish

Simple call:
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

### Other parameters

```
python autotranscribe.py -h
```

```
-i AUDIO, --audio AUDIO	Input audio path
-l LANG,  --lang  LANG  Language (optional if model path is given and no punctuation is desired)
-m MODEL, --model MODEL	Model path (optional)
-o OUT,   --out   OUT   Output path (optional)
-t TOKEN, --token TOKEN	PunkProse token if sending to remote API (optional)
```

### Post-editing on oTranscribe

ASR makes errors. If you want to post-edit the output, go to [otranscribe.com](https://otranscribe.com/), load your audio file and then import one of the template files with the extension `.otr`. 
