# sp2cp

# WIP

### Imageboard bot with recurrent neural network (RNN on GRU)

Бот с нейросетью, обучающейся генерировать комментарии на датасете из тредов с 2ch.hk

---
#### Collect dataset
```
python3 ./grub_threads.py --board=b
```

---
#### Prepare dataset for training
```
python3 ./parse_dataset.py --lexicon_limit=100000 --split=plain --sequence_len=50
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
  --board=b --passcode=passcode --max_threads=30 --use_posts=3 \
  --max_res_len=30
```
