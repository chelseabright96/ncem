import pytest

import ncem.api as ncem
from ncem.estimators import Estimator

from ncem.unit_test.directories import DATA_PATH_ZHANG, DATA_PATH_JAROSCH, DATA_PATH_HARTMANN, DATA_PATH_SCHUERCH, \
    DATA_PATH_LU


class HelperTestEstimator:
    est: Estimator

    def get_estimator(
        self,
        model: str,
        data_origin: str = "zhang",
    ):
        node_label_space_id = "type"
        node_feature_space_id = "standard"
        if model in ["linear_baseline", "linear"]:
            self.est = ncem.train.EstimatorLinear()
        elif model in ["interactions_baseline", "interactions"]:
            self.est = ncem.train.EstimatorInteractions()
        elif model == "ed":
            self.est = ncem.train.EstimatorED()
        elif model == "ed_ncem_max":
            self.est = ncem.train.EstimatorEDncem(cond_type="max")
        elif model == "ed_ncem_gcn":
            self.est = ncem.train.EstimatorEDncem(cond_type="gcn")
        elif model == "ed_ncem2_lr_gat":
            self.est = ncem.train.EstimatorEdNcemNeighborhood(cond_type="lr_gat")
        elif model == "ed_ncem2_gat":
            self.est = ncem.train.EstimatorEdNcemNeighborhood(cond_type="gat")
        elif model == "ed_ncem2_gcn":
            self.est = ncem.train.EstimatorEdNcemNeighborhood(cond_type="gcn")
        elif model == "ed_ncem2_max":
            self.est = ncem.train.EstimatorEdNcemNeighborhood(cond_type="max")
        elif model == "cvae":
            self.est = ncem.train.EstimatorCVAE()
        elif model == "cvae_ncem_max":
            self.est = ncem.train.EstimatorCVAEncem(cond_type="max")
        elif model == "cvae_ncem_gcn":
            self.est = ncem.train.EstimatorCVAEncem(cond_type="gcn")
        else:
            assert False

        if data_origin == "zhang":
            radius = 100
            data_path = DATA_PATH_ZHANG
        elif data_origin == "hartmann":
            radius = 100
            data_path = DATA_PATH_HARTMANN
        elif data_origin.startswith("lu"):
            radius = 100
            data_path = DATA_PATH_LU
        else:
            assert False

        self.est.get_data(
            data_origin=data_origin,
            data_path=data_path,
            radius=radius,
            node_label_space_id=node_label_space_id,
            node_feature_space_id=node_feature_space_id,
        )

    def test_train(self, model: str, data_origin: str = "zhang"):
        self.get_estimator(model=model, data_origin=data_origin)

        kwargs_shared = {
            'optimizer': "adam",
            'latent_dim': 4,
            'dropout_rate': 0.,
            'l2_coef': 0.,
            'l1_coef': 0.,
            'n_eval_nodes_per_graph': 4,
            'scale_node_size': False,
            'output_layer': "gaussian"
        }

        if model == "linear":
            kwargs = {"use_source_type": True, "use_domain": True, "learning_rate": 1e-2}
            train_kwargs = {}
        elif model == "linear_baseline":
            kwargs = {"use_source_type": False, "use_domain": True, "learning_rate": 1e-2}
            train_kwargs = {}
        elif model == "interactions":
            kwargs = {"use_interactions": True, "use_domain": True, "learning_rate": 1e-2}
            train_kwargs = {}
        elif model == "interactions_baseline":
            kwargs = {"use_interactions": False, "use_domain": True, "learning_rate": 1e-2}
            train_kwargs = {}
        elif model == "ed":
            kwargs = {
                "depth_enc": 1,
                "depth_dec": 0,
                "use_domain": True,
                "use_bias": True,
                "learning_rate": 1e-2,
                "beta": 0.1,
            }
            train_kwargs = {}
        elif model in ["ed_ncem_max", "ed_ncem_gcn"]:
            kwargs = {
                "depth_enc": 1,
                "depth_dec": 0,
                "cond_depth": 1,
                "use_domain": True,
                "use_bias": True,
                "learning_rate": 1e-2,
                "beta": 0.1,
            }
            train_kwargs = {}
        elif model == "cvae":
            kwargs = {
                "depth_enc": 1,
                "depth_dec": 1,
                "use_domain": True,
                "use_bias": True,
                "learning_rate": 1e-2,
                "beta": 0.1,
            }
            train_kwargs = {}
        elif model in ["cvae_ncem_max", "cvae_ncem_gcn"]:
            kwargs = {
                "depth_enc": 1,
                "depth_dec": 1,
                "cond_depth": 1,
                "use_domain": True,
                "use_bias": True,
                "learning_rate": 1e-2,
                "beta": 0.1,
            }
            train_kwargs = {}
        elif model.startswith("ed_ncem2"):
            kwargs = kwargs_shared
            kwargs.update({
                "use_domain": True,
                "use_bias": True,
                "learning_rate": 1e-2,
                "cond_type": "lr_gat",
                "dec_intermediate_dim": 0,
                "dec_n_hidden": 0,
                "dec_dropout_rate": float,
                "dec_l1_coef": 0.,
                "dec_l2_coef": 0.,
                "dec_use_batch_norm": False,
            })
            train_kwargs = {}
            self.est.set_input_features(
                h0_in=False,
                target_feature_names=["Abcb4", "Abcc3"],
                neighbor_feature_names=["Adgre1", "Ammecr1"])
        else:
            assert False
        self._model_kwargs = kwargs
        self.est.init_model(**kwargs)
        self.est.split_data_node(validation_split=0.5, test_split=0.5)

        if data_origin == "hartmann":
            batch_size = None
        else:
            batch_size = 16

        if batch_size is None:
            bs = len(list(self.est.complete_img_keys))
            shuffle_buffer_size = None  # None
        else:
            bs = batch_size
            shuffle_buffer_size = int(2)
        self.est.train(
            epochs=5,
            max_steps_per_epoch=2,
            batch_size=bs,
            validation_batch_size=6,
            max_validation_steps=1,
            shuffle_buffer_size=shuffle_buffer_size,
            log_dir=None,
            **train_kwargs
        )
        self.est.model.training_model.summary()


@pytest.mark.parametrize("dataset", ["luwt"])
@pytest.mark.parametrize("model", ["interactions"])
def test_linear(dataset: str, model: str):
    estim = HelperTestEstimator()
    estim.test_train(model=model, data_origin=dataset)


@pytest.mark.parametrize("dataset", ["luwt"])
@pytest.mark.parametrize("model", ["ed_ncem_max"])
def test_ed(dataset: str, model: str):
    estim = HelperTestEstimator()
    estim.test_train(model=model, data_origin=dataset)


@pytest.mark.parametrize("dataset", ["luwt"])
@pytest.mark.parametrize("model", ["cvae_ncem_max"])
def test_cvae(dataset: str, model: str):
    estim = HelperTestEstimator()
    estim.test_train(model=model, data_origin=dataset)


@pytest.mark.parametrize("dataset", ["luwt"])
@pytest.mark.parametrize("model", ["ed_ncem2_max", "ed_ncem2_gcn", "ed_ncem2_lr_gat", "ed_ncem2_gat"])
def test_ed2(dataset: str, model: str):
    estim = HelperTestEstimator()
    estim.test_train(model=model, data_origin=dataset)
