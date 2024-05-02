# Integrating OGC API Processes into Galaxy 

## Background

Galaxy is a tool for creating readily sharable workflows composed of a tool chain. Users can rerun the workflow by uploading their own input files and configuring the input parameters of the tools. The concept of a tool in Galaxy (input -> processing -> output) is very simlilar to the way how OGC API Processes work. Such processes are hosted on the server of a provider and can be triggered by implementing requests which send the input settings to the process and obtain the result once the processing is done. So how can we integrate OGC API Processes into the Galaxy platform allowing users to run these remote processes from Galaxy and connect them to create configurable workflows?

## Concept

First, we tried to wrap a process in a Galaxy tool. To achieve that, we wrote an R script that took over the communication with the remote process and XML file to define the Galaxy tool. While this approach has proven to work (see, e.g., https://toolshed.g2.bx.psu.edu/repository?repository_id=767530b6e7057080) and highly customizable, it is not efficient for servers storing a high number of processes. Every process would require an own tool and deployment process. For this reason, we developed the OGC-API-Process2Galaxy tool. It generates a Galaxy tool that wraps OGC API Processes hosted on a server. The tool requests all processes hosted on the server defined in the config.json. Then, for each process, the tool requests the process description and generates the input parameters, output parameters, and commands. Single processes can be excluded or picked individually by specifying the process names in the corresponding fields in the config.json. The final result is a tool on Galaxy which provides users with a dropdown menu where users can select the process they want to use. Based on the selection, the corresponding UI is shown and users can just start filling the input parameters.

## How to run

Step 1: `git clone https://github.com/AquaINFRA/OGC-API-Process2Galaxy.git` 

Step 2: `cd OGC-API-Process2Galaxy`

Step 3: `npm install`

Step 4: Add the URL to the server hosting the processes to config.json. Optionally, list the server that should be excluded in the corresponding field in the config.json, or pick only individual processes from the server.

Step 5: `python3 OGCProcess2Galaxy.py config.json `

The result is a Galaxy XML file defining the UI for the platform. Together with the R script, we have a Galaxy tool that can be submitted to the Galaxy platform. 

## Limitations

### Performance

The XML file is getting extremely large if there are several hundreds of processes. It worked smoothly on Galaxy for 70 processes but the browser got very slowly (almost not usable) for 700 processes. The truth is probabaly somewhere between these numbers. For servers hosting too many processes, our recommendation is to split the processes into two or more tools. 

To reduce the size a bit, we looked for repetitive patterns which can be replaced using macros. However, at the moment, this requires some manual work after the XML is generated. To do so, search for

  `<option value="uint8">uint8</option>
      <option value="uint16">uint16</option>
      <option value="int16">int16</option>
      <option value="int32">int32</option>
      <option value="float">float</option>
      <option value="double">double</option>` 
in the XML document and replace this section with `<expand macro="out_options"/>`

Another opportunity to reduce the XML size is to search for

  `<option value="image/tiff">image/tiff</option>
      <option value="image/jpeg">image/jpeg</option>
      <option value="image/png">image/png</option>` 
and replace it with `<expand macro="format_options"/>`

