# AITH-hack23
AI Talent Hub Hackathon 2023, Data Driven Life Science track

# ML-Based Biomarker Discovery on Bulk RNA-Seq Data

This tool aims at providing researchers with a more effective and simpler (compared to conventional, non-ML-based [deseq2](https://doi.org/doi:10.18129/B9.bioc.DESeq2)) workflow for detecting 
biomarkers - genes that may indicate a specific biological condition (e.g. disease).

**Team:**
- Fedor Logvin _(ITMO University, Saint Petersburg, Russia)_
- Anton Changailidis _(ITMO University, Saint Petersburg, Russia)_
- Danil Trotsenko _(ITMO University, Saint Petersburg, Russia)_
- Timur Sheydaev _(ITMO University, Saint Petersburg, Russia)_
- Xenia Sukhanova _(ITMO University, Saint Petersburg, Russia)_

---

- [ML Pipeline](#sec1) </br>
- [System requirements](#sec2) </br>
- [Deployment](#sec3) </br>

<a name="sec1"></a>
## ML Pipeline

The analysis consists of following steps:
1. A maximum-based low counts filter (Rau et al.) to eliminate genes with low counts.
2. Bayesian search to obtain the best hyperparameters values for XGboost.
3. Model gets fitted on a specified number of random subsamples of 80% from row count, using the best hyperparametes discovered earlier.
4. For both models, (n_obs) important genes are retained from each iteration; at the end all genes which occur in specified number of iterations are kept.
5. To identify, whether expression of selected genes significantly differs within defined groups, Mann-Whitney U test is performed. FDR is controlled at level a=0.05.


<a name="sec2"></a>
## System requirements

- Custom Rau filter written in C# requires a .NET framework, which can be found [here](https://dotnet.microsoft.com/en-us/download).
- Python 3.9+ is recommended, older versions were not tested.
- Required python packages can be found in requirements.txt. Keep in mind that scikit-optimize requires older NumPy versions(~1.23.5).

<a name="sec3"></a>
## Deployment
TODO update with job scheduler info
- Specify Telegram bot token and a logging directory in config.toml
- On Linux, install systemctl services for Dash app and Telegram bot. To do this, copy service config files to /lib/systemd/
- Run systemctl services
