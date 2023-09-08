### Project wiki
> (You can also check out our [GitHub](https://github.com/TSheyd/AITH-hack23) for technical details)

----
#### What is this?
This tool can help You search for potential biomarker genes in bulk RNA-seq data.

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
    
   - Gene - 
   - Group - 
   - P-value - 
   - Adjusted P-Value - 


2. **Heatmap**
    
    Heatmap is used to visually compare counts between different genes. 
In case several groups are detected, borderlines between them are drawn. 
You can compare specific genes by selecting them in the table (or filtering by column value) and pressing the "Update Graph" button.


3. **Violin plot**

    Violin plot can be activated by selecting a row of the table. Violin plots show 


#### How is it better than conventional tools like deseq2?
We propose that using ML lets us achieve lower FNR (False Negative Rate) 
on our results, thus achieving better efficiency in searching for biomarkers. 

Also, this tool, being no-code, is much easier to use, since practically all other tools require either RStudio or at least command line skills.




