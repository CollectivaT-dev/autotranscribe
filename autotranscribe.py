#!/usr/bin/env python3

from vosk import Model, KaldiRecognizer, SetLogLevel
import sys
import os
import json
import subprocess
import argparse
import requests
import httpx
import zipfile
from math import modf

parser = argparse.ArgumentParser(description="Punctuation prediction analyzer.")
parser.add_argument('-i', '--audio', type=str, required=True, help='Input audio path')
parser.add_argument('-l', '--lang', type=str, help='Language')
parser.add_argument('-m', '--model', type=str, help='Model path')
parser.add_argument('-o', '--out', type=str, help='Output path')
parser.add_argument('-t', '--token', type=str, help='PunkProse token if sending to remote API')

MODEL_DIR = 'models'
MODEL_PATH_DICT = { 'en':'models/vosk-model-small-en-us-0.15', 
                    'tr':'models/vosk-model-small-tr-0.3', 
                    'ca':'models/vosk-model-small-ca-0.4', 
                    'es':'models/vosk-model-small-es-0.3'}

MODEL_URL_DICT = {'en': 'http://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip', 
                  'ca': 'https://alphacephei.com/vosk/models/vosk-model-small-ca-0.4.zip', 
                  'tr': 'https://alphacephei.com/vosk/models/vosk-model-small-tr-0.3.zip',
                  'es': 'https://alphacephei.com/vosk/models/vosk-model-small-es-0.3.zip'}

CONFIDENCE_THRESHOLD = 0.8
SAMPLE_RATE=16000
MAXREQUESTSIZE=2000
LOCAL_PUNKPROSE_URL = "http://localhost:8001/api/v1/punctuate"
API_PUNKPROSE_URL = "http://api.collectivat.cat/punkProse"
OUTPUT_JSON = True #For debugging
SEND_TO_PUNKPROSE = True #For debugging

def wordinfos_to_otr(wordinfos):
    otr_text = ""
    sentence_start = False

    for w in wordinfos:
        if w['confidence'] < CONFIDENCE_THRESHOLD or sentence_start:
            wordstart = "{:.2f}".format(float(w['startTime']['seconds']) + w['startTime']['nanos']/10e8)
            otr_text += '<span class=\"timestamp\" data-timestamp=\"' + wordstart + '\"></span> '
            otr_text += w['word'] + ' '
            sentence_start = False
        else:
            otr_text += w['word'] + ' '
            
        if w['word'][-1] in ['.', '?']:
            sentence_start = True

    otr_format_dict = {'text': otr_text, "media": "", "media-time":"0.0"}

    return otr_format_dict


def vosk_to_PunkProse_JSON(words):
    wordinfos = []
    for word in words:
        startinfo = modf(word['start'])
        endinfo = modf(word['end'])
        wordinfo = {"startTime":{"seconds":str(int(startinfo[1])),"nanos":int(startinfo[0]*10e8)},
                "endTime":{"seconds":str(int(endinfo[1])),"nanos":int(endinfo[0]*10e8)},
                "word":word['word'],  
                "confidence":word['conf']}
        
        wordinfos.append(wordinfo)
    return wordinfos


if __name__ == "__main__":
    args = parser.parse_args()

    model_path = args.model
    audio_path = args.audio
    out_path = args.out
    token = args.token
    lang = args.lang

    filename = os.path.splitext(os.path.basename(audio_path))[0]

    #Checks
    if not lang:
        print("WARNING: Language not specified (-l). Will skip punctuation.")
        # if not model_path:
        #     print("ERROR: ASR model path (-m) not specified either.")
        #     sys.exit()

    if not out_path:
        out_path = os.path.dirname(audio_path)
        print("WARNING: Output directory not specified (-o). Will put results to audio directory.")
    else:
        if os.path.exists(out_path):
            if not os.path.isdir(out_path):
                print("ERROR: %s is a file"%out_path)
                sys.exit()
        else:
            os.mkdir(out_path)

    if not model_path:
        if lang in MODEL_PATH_DICT:
            model_path = MODEL_PATH_DICT[lang]
            if not os.path.exists(model_path):
                if not os.path.exists(MODEL_DIR):
                    os.mkdir(MODEL_DIR)

                #Download model
                path_to_zip_file = model_path + '.zip'
                if not os.path.exists(path_to_zip_file):
                    r = requests.get(MODEL_URL_DICT[lang])
                    if r.status_code == 200:
                        with open(path_to_zip_file, 'wb') as f:
                            f.write(r.content)

                with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
                    zip_ref.extractall(MODEL_DIR)
        else:
            print("ERROR: Language %s not in MODEL_PATH_DICT. Either add there or manually specify model directory (-m)."%lang)
            sys.exit()


    if not token:
        print("WARNING: No API token (-t) specified. If service is not found locally, punctuation will be skipped.")




    # Convert audio to WAV
    try:
        process = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i',
                                    audio_path,
                                    '-ar', str(SAMPLE_RATE) , '-ac', '1', '-f', 's16le', '-'],
                                    stdout=subprocess.PIPE)
    except:
        print("ERROR: Problem converting audio. Make sure ffmpeg is installed")
        sys.exit()


    # Do recognition with VOSK
    print("Loading Kaldi model:", model_path)
    model = Model(model_path)
    rec = KaldiRecognizer(model, SAMPLE_RATE)
    SetLogLevel(0)

    results = []
    words = []
    while True:
        data = process.stdout.read(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            #print(rec.Result())
            segment_result = json.loads(rec.Result())
            results.append(segment_result)

            if 'result' in segment_result:
                words.extend(segment_result['result'])
    final_result = json.loads(rec.FinalResult())
    results.append(final_result)
    if 'result' in final_result:
        words.extend(final_result['result'])

    # # #-----dbg------
    # with open("/Users/alp/Documents/TWB/play/transcription_tool/temp.json", 'r') as f:
    #     words = json.loads(f.read())
    # #-----dbg------

    #Write raw versions to disk
    raw_txt_path = os.path.join(out_path, filename + '.raw.txt')
    with open(raw_txt_path, 'w') as f:
        for w in words:
            f.write(w['word'] + " ")
        print("Raw txt:", raw_txt_path)


    raw_otr_path = os.path.join(out_path, filename + '.raw.otr')
    rawwordinfos = vosk_to_PunkProse_JSON(words)
    otr_format_dict = wordinfos_to_otr(rawwordinfos)
    with open(raw_otr_path, 'w') as f:
        f.write(json.dumps(otr_format_dict))
        print("Raw OTR:", raw_otr_path)


    if OUTPUT_JSON:
        raw_json_path = os.path.join(out_path, filename + '.raw.json')
        with open(raw_json_path, 'w') as f:
            f.write(json.dumps(words, ensure_ascii=False))
        print("Raw JSON:", raw_json_path)


    # Convert to PunkProseAPI JSON
    wordinfos = vosk_to_PunkProse_JSON(words)
    
    # Send to PunkProse
    punctuation_successful = False
    if SEND_TO_PUNKPROSE and lang:
        #Split into chunks of 2000 words so that API can process (max 3000 words)
        #TODO: this split can be smarter
        wordinfochunks = [wordinfos[i:i+MAXREQUESTSIZE] for i  in range(0, len(wordinfos), MAXREQUESTSIZE)]
        request_strings = [json.dumps(wordinfochunk) for wordinfochunk in wordinfochunks]

        # #-----dbg------
        # for i, request_string in enumerate(request_strings):
        #     with open("request_string." + str(i) +".txt", 'w') as f:
        #         f.write(request_string)
        # #-----dbg------

        puncdwordinfos = []
        for request_string in request_strings:
            json_data = {'source':request_string, 
                         'type':'json',  
                         'lang':lang,
                         'recase':True}
            if token:
                service_url = API_PUNKPROSE_URL
                json_data['token'] = token
            else:
                service_url = LOCAL_PUNKPROSE_URL

            print("Punctuation call to", service_url)

            try:
                r = httpx.post(service_url, json=json_data, timeout=None)
                if r.status_code == 200:
                    punkProseResponse = r.json()
                    puncdwordinfos.extend(json.loads(punkProseResponse['result']))
                    punctuation_successful = True
                else:
                    error = r

                    print("Error while processing punctuation request.")
                    print(error)
                    try:
                        print(r.json()['detail'])
                    except:
                        pass
                    punctuation_successful = False
                    break

            except httpx.HTTPError as exc:
                print(f"Error while requesting {exc.request.url!r}.")
                print(exc)
                punctuation_successful = False
                break
    
    if punctuation_successful:
        print("Punctuation successful.")

        # Output everything to files
        otr_path = os.path.join(out_path, filename + '.otr')
        otr_format_dict = wordinfos_to_otr(puncdwordinfos)
        with open(otr_path, 'w') as f:
            f.write(json.dumps(otr_format_dict))
            print("Punctuated OTR:", otr_path)

        txt_path = os.path.join(out_path, filename + '.txt')
        with open(txt_path, 'w') as f:
            for w in puncdwordinfos:
                f.write(w['word'] + " ")
            print("Punctuated TXT:", txt_path)

        if OUTPUT_JSON:
            json_path = os.path.join(out_path, filename + '.json')
            with open(json_path, 'w') as f:
                f.write(json.dumps(puncdwordinfos, ensure_ascii=False))
            print("Punctuated JSON:", json_path)
    else:
        print("Punctuation failed.")

    print("Done...")
