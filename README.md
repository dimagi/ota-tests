# ota-tests
Suite of black box tests for the CommCare OTA endpoints

## Running the test

1. Copy the `config.ini` file and update it with your configuration. You can use the same config file
for multiple services. Each service must have its own section in the config.
2. From the command line run:
```
CONFIG=my_config.ini SECTION=my_service py.test
```

You can specify individual tests to run by using the `-k EXPRESSION` pytest command line option.
