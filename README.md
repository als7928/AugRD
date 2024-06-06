## Python environment setup with Conda
Install torch, torch-sparse torch-geometric, torch-scatter, torchdiffeq, ...
---
## Run
```
$ python main.py --dataset MUTAG --epochs 200 --time 2 --hidden_dim 128
```

## Ablation
```
$ python main.py --dataset MUTAG --ablation_study no_aug

```

## visualization
```
$ python main.py --dataset MUTAG --drawing True

```
The visualization results are saved as sample.png in the root folder every 50 epochs.