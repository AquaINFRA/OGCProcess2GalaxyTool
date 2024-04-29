# Integrating OGC API Processes into Galaxy 

This tool generates a Galaxy tool that wraps OGC API Processes. The tool first iterated through the list of servers listed in the config.json and requests all processes hosted on the server. For each process, the tool requests the process description and generates the input parameters, output parameters, and commands. Processes can be excluded or limited using the corresponding fields in the config.json. 
The workflow to get the tool into Galaxy is as follows:

- Fill the config.json
- Run the tool
- Make a Pull Request to Galaxy
