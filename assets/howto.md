### Project wiki
> (You can also check out our [GitHub](https://github.com/TSheyd/AITH-hack23) for technical details)

----
### What is this?
This tool can help You search for potential biomarker genes in bulk RNA-seq data. 
Biomarkers are extremely useful, since they can provide scientists with insight on directions and targets of further research.

### How do I use this?
#### Loading data
You can check out a sample input [here]() 

Using the **"Submit File"** form, load your file and specify the minimal gene 
observation value (10 by default). 

Next, press **"Submit"** and confirm in our [Telegram bot](https://t.me/koshmarkersbot) 
(pressing the button will lead you there). After the file is processed, you will recieve a notification there.

#### Analyzing results

Calculation results are presented in several forms:

1. **Table**
    
   - Gene - gene from the dataset. Clicking on its name will send You to [NCBI Gene Library](https://www.ncbi.nlm.nih.gov/gene/) page
   - Group - test design for P-Value
   - P-value - of a test described in Group column
   - Adjusted P-Value - [FDR-adjusted](https://en.wikipedia.org/wiki/False_discovery_rate#Benjamini%E2%80%93Hochberg_procedure) p-value


2. **Heatmap**

    Heatmap is used to visually compare counts between different genes. You can compare specific genes by selecting them in the table (or filtering by column value) and pressing the "Update Graph" button.

3. **Violin plot**

    Violin plot can be activated by selecting a row of the table. Violin plots show count distribution of a gene in different test groups

You can also download the results by clicking "Download tables" button.

### How is it better than conventional tools like [deseq2](https://doi.org/doi:10.18129/B9.bioc.DESeq2)?
We propose that using ML lets us achieve lower FNR (False Negative Rate) 
on our results, thus achieving better efficiency in searching for biomarkers. 

Also, this tool, being no-code, is **much** easier to use, since practically all other tools require either RStudio or at least command line skills.
