
import os
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint
from torch_data.datasets.hartmann import Hartmann
from model import GraphEmbedding
from torch_geometric import loader
from torch_geometric.data import Data
import numpy as np
from utils.argparser import parse_args


def main():
    args, arg_groups = parse_args(GraphEmbedding)

    # Checkpoint settings
    checkpoint_callback = ModelCheckpoint(
        dirpath=os.path.join(os.path.dirname(__file__), 'checkpoints'),
        save_top_k=1,
        verbose=False,
        monitor="val_loss",
        mode="min",
    )
    # TODO: improve check-pointing stuff.
    # Create a PyTorch Lightning trainer with the generation callback

    # Choosing the dataset
    if args.dataset == "hartmann":
        # A transform function just for this use case
        def _transform_hartmann_ncem(data: Data):
            if data.transform_done:
                return data
            return Data(
                x=data.cell_type,
                edge_index=data.edge_index,
                transform_done=True,
                num_nodes=data.cell_type.shape[0],
            )

        dataset = Hartmann(args.data_path, transform=_transform_hartmann_ncem)
        # TODO: Do test
        # TODO: Distribute better
        np.random.seed(42)
        idxs = np.arange(len(dataset))
        np.random.shuffle(idxs)
        dataset = dataset[idxs]
        split = int(0.9 * len(dataset))
        train_dataset, val_dataset = dataset[:split], dataset[split:]

        train_dataloader = loader.DataListLoader(
            train_dataset,
            num_workers=args.num_workers,
            shuffle=True,
            batch_size=args.batch_size,
        )
        val_dataloader = loader.DataListLoader(
            val_dataset,
            num_workers=args.num_workers,
            batch_size=args.batch_size
        )
        n_input_features = train_dataset[0].num_features

    else:
        raise NotImplementedError()

    model = GraphEmbedding(
        num_features=n_input_features,
        **vars(arg_groups["GraphEmbedding"]))
    trainer: pl.Trainer = pl.Trainer.from_argparse_args(args, callbacks=[checkpoint_callback])
    trainer.fit(model=model, train_dataloaders=train_dataloader, val_dataloaders=val_dataloader)


if __name__ == "__main__":
    main()
