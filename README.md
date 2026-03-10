## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Author:** Diego Paredes  
**Degree project (PUCP, 2022-1)**  
**Focus:** Deep learning for **precipitation quality control (QC)** using **GOES-16 satellite imagery**.

# Deep Learning–Based Precipitation Quality Control System  (Version 1.0.0)

Between 2020 and 2021, the Peruvian National Meteorological and Hydrological Service (SENAMHI) collected approximately 3.5 million precipitation records from a nationwide network of automatic weather stations.
Out of the total observations, the existing automated Quality Control (QC) system flagged around 4% of the data as suspicious due to extreme values. However, only 53% of these records were manually validated in a timely manner, mainly due to operational and resource constraints.
To address this limitation, this project proposes a Deep Learning–based quality control system that leverages GOES‑16 satellite imagery and auxiliary data to validate extreme precipitation observations in near real time.
The proposed approach relies on a CNN‑RNN architecture, trained using labels generated from the manual QC process, with the goal of supporting and accelerating data validation workflows, reducing operational burden, and improving the availability of reliable precipitation data for hydrometeorological analysis.

---


## Environment
- Python 3.11
- pip 26.x recommended


## Repository Structure

.
├── configs/        # Experiment configurations (YAML)
├── data/           # raw/interim/processed datasets (not versioned)
├── outputs/        # models, metrics, figures, logs (generated)
├── notebooks/      # EDA + results + interpretability (CAM/heatmaps)
├── scripts/        # CLI entrypoints to run pipelines
└── src/            # Reusable core code (data, models, training)