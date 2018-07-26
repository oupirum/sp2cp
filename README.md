# sp2cp

# WIP

### Imageboard bot with recurrent neural network (RNN on GRU)

Бот с нейросетью, обучающейся генерировать комментарии на датасете из тредов с 2ch.hk


#### JUST FOR LULZ

![Screenshot](https://drive.google.com/uc?id=1vsmu5BQSC8GfxAzsnwU6KhJEtNyo7SA6)
![Screenshot](https://drive.google.com/uc?id=1vDCcYoNY76-_cH0g2viereSBte2Z5HI-)
![Screenshot](https://drive.google.com/uc?id=1LnCpnoQ6f2bv76zYqOc28Fat4d2SOu0k)

https://drive.google.com/drive/folders/1Xmm5DTxQ8sJwL2ygefWTPFWsTSviMPDP

---
### How to run
---
#### Collect dataset
```
python3 ./grub_threads.py --board=b
```

---
#### Prepare dataset for training
```
python3 ./parse_dataset.py --lexicon_limit=100000 --sequence_max_len=50
```
It will save tokenized dataset and id2token map in `./dataset/parsed/` directory.

---
#### Train
```
python3 ./train.py --epochs=20 --batch_size=100
```
After training you can find trained models and id2token map in `./models/` directory.

---
#### Run autoposter
```
python3 ./autoposter.py --weights_file=./models/weights.h5 --id2token_file=./models/id2token.json \
  --board=b --passcode=passcode --max_threads=30 \
  --max_res_len=30
```
