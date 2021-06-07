
## Commands

`qi` consists of multiple sub-commands:

* describe
* logs
* open
* scaffold

Generally, `qi` supports abbreviated commands, for example `qi l` can be used instead of `qi logs`.


### describe

Get description of a SageMaker resource using [rich](https://github.com/willmcgugan/rich)
terminal formatting. 

* Argument:
    * SageMaker Resource ARN

* Options:
    * `--profile` / `-p` of AWS config or credentials file, default: None, type: str

Example usage:

    qi open <training_job_arn> -p

Example output:

    https://eu-west-1.console.aws.amazon.com/sagemaker/home?region=eu-west-1#/jobs/<training_job_id>


### logs

Logs support three subcommands, which all operate on SageMaker Resource ARNs:


#### logs cat

Fetches all logstream events of SageMaker Resource.

* Argument:
    * SageMaker Resource ARN

* Options:
    * `-f` / `--follow` flag to keep fetching new logs, default: False  
    * `-i` / `--interval` set interval to fetch new logs when `--follow` flag 
      is set, default: 10, 
      type: int
    * `--profile` / `-p` of AWS config or credentials file, default: None, 
      type: str

Example usage:

    qi logs cat -f -i 30 <training_job_arn>


#### logs tail

Fetches last logstream events of SageMaker Resource.

* Argument:
    * SageMaker Resource ARN

* Options:
    * `-n` number of lines to fetch, default: 10
    * `-f` / `--follow` flag to keep fetching new logs, default: False
    * `-i` / `--interval` set interval to fetch new logs when `--follow` flag
      is set, default: 10,
      type: int
    * `--profile` / `-p` of AWS config or credentials file, default: None,
      type: str

Example usage:

    qi logs tail -f -n 5 <training_job_arn>


#### logs head

Fetches first logstream events of SageMaker Resource.

* Argument:
    * SageMaker Resource ARN

* Options:
    * `-n` number of lines to fetch, default: 10
    * `--profile` / `-p` of AWS config or credentials file, default: None,
      type: str

Example usage:

    qi logs head -n 5 <training_job_arn>

#### logs filter

Fetches filtered logstream events of SageMaker Resource.

* Argument:
    * SageMaker Resource ARN

* Options:
    * `--expression` / `-e` to filter for, default: None, type: str, required
    * `--profile` / `-p` of AWS config or credentials file, default: None, type: str
    
Example usage:

    qi logs filter -e <expression> <training_job_arn>

### open

Open a training or hpo job in the browser or print its url to the console.

* Argument:
    * SageMaker Resource ARN

* Options:
    * `--print` or `-p`, returns the url only to the console

Example usage:

    qi open <training_job_arn> -p

Example output:

    https://eu-west-1.console.aws.amazon.com/sagemaker/home?region=eu-west-1#/jobs/24964125--0--2020-07-09--22-40-41-572296

### scaffold

Generates either a scaffold folder structure for an empty TrainingJob or downloads the `/opt/ml` folder of a submitted TrainingJob.

* Argument:
    * path to new folder

* Options:
    * `--arn` of a SageMaker TrainingJob
    * `--profile` / `-p` of AWS config or credentials file, default: None, type: str

Example usage:

    qi scaffold <path/to/new/folder> --arn <training_job_arn>

Example folder structure of downloaded folder:

    .
    └── input
        ├── config
        │   ├── hyperparameters.json
        │   └── inputdataconfig.json
        └── data
            ├── test
            │   └── test.json
            └── train
                └── train.json


