<font size = 7><center><b><u>Initia Validators Metrics Parser</u></b></center></font>
### The Initia Metrics Parser is a Python script designed to analyze validator-related metrics from the Initia blockchain network. It fetches data from blockchain nodes via RPC and API endpoints, processes blocks within specified heights, and provides insights into validator activities and network participation.

> The Initia Metrics Parser gathers the following metrics for each validator:
- **Total Signed Blocks**: Number of blocks signed by the validator.
- **Total Missed Blocks**: Number of blocks missed by the validator.
- **Total Proposed Blocks**: Number of blocks proposed by the validator.
- **Oracle Votes**: Number of oracle votes submitted by the validator.
- **Missed Oracle Votes**: Number of oracle votes missed by the validator.
- **Slashing History**: Detailed slashing history including height and verification data when the valdiator was jailed.
- **Governance Participation**: All proposals voted on by the validator, including transaction hashes, vote options and heights.
- **Validator Creation Info**: Height and hash of the block of the validator creation transaction.
- **Delegators Number**: Number of delegators assigned to the validator.
- **Tombstoned Validators**

> You can view the parsed metrics by this script at:
- [**Parsed Metrics (JSON format)**](https://metrics.trusted-point.com/initia/metrics.json)
- [**User-Friendly Display**](https://metrics.trusted-point.com/initia/)
- **In this example blocks signing and oracle voting stats are parsed for the 800 000 - 2 051 430 blocks range**
[<img src='assets\ui.png' alt='banner' width= '90.5%'>]()

# Installation
## 1. Clone the repository:
```bash
git clone https://github.com/trusted-point/Initia-Metrics.git
```
## 2. Navigate to the project directory:
```bash
cd Initia-Metrics
```
## 3. Install the required Python packages:
```py
pip3 install -r requirements.txt
```
## 4. Copy the example configuration file and edit it as needed:
```bash
cp config_example.yaml config.yaml
```
## 5. Open config.yaml in your preferred text editor and make the necessary changes:

```bash
nano config.yaml
```
The config.yaml file contains various settings that you can customize to suit your needs. Below is an explanation of each setting:
```yaml
rpc: "http://127.0.0.1:21657"  # The RPC endpoint for connecting to the blockchain node.
api: "http://127.0.0.1:1311"  # The API endpoint for accessing blockchain data.
bech_32_prefix: "init"  # The prefix used for Bech32 addresses in the blockchain.
max_number_of_valdiators_ever_in_the_active_set: 100  # The maximum number of validators that have ever been in the active set.
batch_size: 100  # The number of blocks to process in each batch.
multiprocessing: true  # Enable or disable multiprocessing for faster data processing.
start_height: 800000  # The starting block height for the analysis. (OPTIONAL. The script will fetch lowest available height on the provided RPC endpoint)
end_height: 2051430  # The ending block height for the analysis.  (OPTIONAL. The script will fetch highest available height on the provided RPC endpoint)
log_lvl: "DEBUG"  # The logging level (e.g., DEBUG, INFO, WARNING, ERROR).
metrics:
  governance_participation: True  # Enable analysis of governance participation.
  delegators: True  # Enable analysis of delegators.
  validator_creation_block: True  # Enable tracking of validator creation blocks.
  jails_info: True  # Enable gathering information about jails.
```
## 6. Starting the script
```py
python3 main.py
```
[<img src='assets\terminal.png' alt='terminal' width= '99.5%'>]()

## Additional Commands:
### Reset block-related metrics:
- If you need to reset the metrics stored in metrics.json, use the following command:
```py
python3 reset_blocks_metrics.py
```
### Generate a table of metrics in the terminal:
- To display the metrics in a tabular format in the terminal, use the following command:
```py
python3 table.py
```
```bash
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|   # | Moniker                        |   Total Signed Blocks |   Total Missed Blocks |   Total Oracle Votes |   Total Missed Oracle Votes |   Jails Number |   Voted Proposals |
+=====+================================+=======================+=======================+======================+=============================+================+===================+
|   1 | Keplr                          |               1250394 |                  1036 |              1249269 |                        2161 |              0 |                 0 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|   2 | B-Harvest                      |               1249734 |                  1696 |              1249129 |                        2301 |              1 |                25 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|   3 | 01node                         |               1249370 |                  2060 |              1248822 |                        2608 |              3 |                 0 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|   4 | Cosmostation                   |               1249052 |                  2378 |              1087635 |                      163795 |              3 |                17 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|   5 | Lavender.Five Nodes honeybee   |               1248919 |                  2511 |               549967 |                      701463 |              2 |                 2 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|   6 | polkachu.com                   |               1248590 |                  2840 |               955604 |                      295826 |              2 |                 3 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|   7 | Anomaly                        |               1248212 |                  3218 |              1233797 |                       17633 |             10 |                 1 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|   8 | Coinage x DAIC                 |               1248138 |                  3292 |              1247305 |                        4125 |              4 |                21 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|   9 | P-ops Team                     |               1246709 |                  4721 |              1244600 |                        6830 |              2 |                 7 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|  10 | BwareLabs                      |               1245697 |                  5733 |              1241581 |                        9849 |              2 |                 5 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|  11 | init.r                         |               1245389 |                  6041 |              1243187 |                        8243 |              3 |                18 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|  12 | Upnode                         |               1245174 |                  6256 |               966845 |                      284585 |              4 |                15 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|  13 | Lewdeus Labs                   |               1244319 |                  7111 |              1242455 |                        8975 |              5 |                28 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|  14 | WhisperNode zipper-mouth_face  |               1242673 |                  8757 |               964627 |                      286803 |              3 |                29 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|  15 | Shinlabs                       |               1242242 |                  9188 |              1241743 |                        9687 |              5 |                 0 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|  16 | Felix                          |               1242144 |                  9286 |              1239056 |                       12374 |              0 |                 0 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|  17 | Nodes.Guru                     |               1240768 |                 10662 |               505783 |                      745647 |              1 |                 4 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|  18 | 1XP  0base.vc                  |               1240110 |                 11320 |              1231212 |                       20218 |              8 |                17 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|  19 | Oni shinto_shrine              |               1239486 |                 11944 |              1238055 |                       13375 |              2 |                 7 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|  20 | SCV-Security                   |               1237736 |                 13694 |              1220710 |                       30720 |              3 |                 2 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
|  21 | TrustedPoint                   |               1236787 |                 14643 |              1235922 |                       15508 |              1 |                11 |
+-----+--------------------------------+-----------------------+-----------------------+----------------------+-----------------------------+----------------+-------------------+
```
