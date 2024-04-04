import json
import xml.etree.ElementTree as ET
import urllib.request 
import warnings
import sys

#OGC Process Description types to Galaxy Parameter types
typeMapping = {
  "array": "?",
  "boolean": "boolean",
  "integer": "integer",
  "number": "float",
  "object": "data",
  "string": "text"
}

#conformance classes 
confClasses = [
"http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core",
"http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/ogc-process-description",
"http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/json"
]

def OGCAPIProcesses2Galaxy(configFile: str) -> None:
    """
    Function to convert processes form a given list of 
    OGC API Processes instances to Galaxy tools. 

    Parameters:
    configFile (str): Path to config file which specifies the instances as well as 
    included and excluded services. Example: 
    [
        {
            "server_url": "https://someOGCAPIProcessesInstace/api/",
            "included_services": ["*"],
            "excluded_services": ["process1", "process45"]
        }
    ]

    Returns:
    None: Function has no return value. Converted processes are stores as .xml-files.
    """

    #add tool
    tool = ET.Element("tool") 
    tool.set('id', "generic_ogc_processes_wrapper")
    tool.set('name', "Generic OGC Processes Wrapper")
    tool.set('version', "0.1.0")

    #add description
    description = ET.Element("description") 
    description.text = "executes OGC API Processes"
    tool.append(description) 

    #add exit code
    stdio = ET.Element("stdio") 
    exitCode = ET.Element("exit_code")
    exitCode.set("range", "1:") 
    stdio.append(exitCode) 
    tool.append(stdio)

    #add requriements
    requirements = ET.Element("requirements")
    requirement1 = ET.Element("requirement")
    requirement1.set("type", "package")
    requirement1.set("version", "4.1.2")
    requirement1.text = "R"

    requirement2 = ET.Element("requirement")
    requirement2.set("type", "package")
    requirement2.set("version", "0.2.3")
    requirement2.text = "httr2"

    requirement3 = ET.Element("requirement")
    requirement3.set("type", "package")
    requirement3.set("version", "1.2.0")
    requirement3.text = "getopt"

    requirement4 = ET.Element("requirement")
    requirement4.set("type", "package")
    requirement4.set("version", "1.8.7")
    requirement4.text = "jsonlite"

    requirements.append(requirement1)
    requirements.append(requirement2)
    requirements.append(requirement3)
    requirements.append(requirement4)

    tool.append(requirements)

    #add command
    command = ET.Element("command")
    command.text = "<![CDATA[ Rscript $__tool_directory__/generic.R --file $file ADD INPUT PARAMETERS ]]>" # not yet parsed correctly in xml
    tool.append(command)

    #add inputs
    inputs = ET.Element("inputs")

    #add outputs
    outputs = ET.Element("ouputs")

    #load config
    with open(configFile) as configFile:
        configJSON = json.load(configFile)

    conditional_server = ET.Element("conditional")
    conditional_server.set("name", "conditional_server")
    select_server = ET.Element("param")
    select_server.set("name", "select_server")
    select_server.set("type", "select")
    select_server.set("label", "Select server")

    index_i = 0
    for api in configJSON: 
        index_i += 1
        #check conformance
        with urllib.request.urlopen(api["server_url"] + "conformance") as conformanceURL:
            conformanceData = json.load(conformanceURL)
            
            for confClass in confClasses:
                if confClass not in confClasses:
                    msg = "Specified API available via:" + baseURL + " does not conform to " + confClass + "." + "This may lead to issues when converting its processes to Galaxy tools."
                    warnings.warn(msg, Warning)

        server = ET.Element("option")
        server.text = api["server_url"]
        server.set("value", api["server_url"])
        select_server.append(server)

        #make sure select-server dropdown is at the beginning
        if index_i == len(configJSON):
            conditional_server.append(select_server)

        when_server = ET.Element("when")
        when_server.set("value", api["server_url"])

        conditional_process = ET.Element("conditional")
        conditional_process.set("name", "conditional_process")
        select_process = ET.Element("param")
        select_process.set("name", "select_process")
        select_process.set("type", "select")
        select_process.set("label", "Select process")

        with urllib.request.urlopen(api["server_url"] + "processes") as processesURL:
            processesData = json.load(processesURL)
            
            index_j = 0
            when_list = []
            for process in processesData["processes"][0:50]: #only get 50 processes!
                #check if process is excluded
                if(process["id"] in api["excluded_services"]):
                    continue

                #check if process is included
                if(process["id"] in api["included_services"] or ("*" in api["included_services"] and len(api["included_services"]) == 1)):
                    index_j += 1
                    if len(processesData["processes"]) == 0:
                        msg = "Specified API available via:" + baseURL + " does not provide any processes."
                        warnings.warn(msg, Warning)

                    with urllib.request.urlopen(api["server_url"] + "processes/" + process["id"]) as processURL:
                        process = json.load(processURL)
                        processElement = ET.Element("option")
                        processElement.text = process["title"]
                        processElement.set("value", process["id"])
                        select_process.append(processElement)

                        when_process = ET.Element("when")
                        when_process.set("value", process["id"])

                        #iterate over process params
                        for param in process["inputs"]:
                            process_input = ET.Element("param")

                            #set param name
                            process_input.set("name", param) 
                            
                            #set param title
                            if "title" in process["inputs"][param].keys():
                                    process_input.set("label", param)
                            else:
                                msg = "Parameter " + paramID + " of process " + toolID + " has not title attribute."
                                warnings.warn(msg, Warning)
                                process_input.set("name", "?")
                            
                            #set param description
                            if "description" in process["inputs"][param].keys():
                                process_input.set("help", process["inputs"][param]["description"])
                            else:
                                msg = "Parameter " + paramID + " of process " + toolID + " has not description attribute."
                                warnings.warn(msg, Warning)
                                process_input.set("help", "No description provided!")

                            #set param type
                            if 'type' in process["inputs"][param]["schema"].keys(): #simple schema
                                if process["inputs"][param]["schema"]["type"] in typeMapping.keys():
                                    process_input.set("type", typeMapping[process["inputs"][param]["schema"]["type"]])
                            elif 'oneOf' in process["inputs"][param]["schema"].keys(): #simple schema
                                isComplex = True
                                paramFormats = ""
                                for format in process["inputs"][param]["schema"]["oneOf"]:
                                    if format["type"] == "string":
                                        process_input.set("type", typeMapping["string"])
                                        process_input.set("format", format["contentMediaType"])
                                    if format["type"] == "object":
                                        process_input.set("type", typeMapping["object"])
                            else:
                                msg = "Parameter " + paramID + " of process " + toolID + " has no simple shema."
                                warnings.warn(msg, Warning)

                            when_process.append(process_input)

                        when_list.append(when_process)

                        print(process["id"])
        conditional_process.append(select_process)
        for when in when_list:
            conditional_process.append(when)    
        when_server.append(conditional_process)
    conditional_server.append(when_server)
    '''
    #get processes
                    
                    if(process["id"] in api["excluded_services"]):
                        continue

                    if(process["id"] in api["included_services"] or ("*" in api["included_services"] and len(api["included_services"]) == 1)):

                        toolID = process["id"]
                        toolName = process["title"]
                        toolVersion = process["version"]
                        print(toolID)
                        
                        isComplex = False

                        
                
                        #add inputs
                        inputs = xml.etree.ElementTree.Element("inputs") 
                        
                        
                        #add params
                        for param in process["inputs"]:
                            paramID = param

                            #add param title
                            if "title" in process["inputs"][param].keys():
                                paramTitle = process["inputs"][param]["title"]
                            else:
                                msg = "Parameter " + paramID + " of process " + toolID + " has not title attribute."
                                warnings.warn(msg, Warning)
                                paramTitle = "?"

                            if "description" in process["inputs"][param].keys():
                                paramDescription = process["inputs"][param]["description"]
                            else:
                                msg = "Parameter " + paramID + " of process " + toolID + " has not description attribute."
                                warnings.warn(msg, Warning)
                                paramDescription = "No description provided!"

                            #add param type
                            if 'type' in process["inputs"][param]["schema"].keys(): #simple schema
                                if process["inputs"][param]["schema"]["type"] in typeMapping.keys():
                                    paramType = typeMapping[process["inputs"][param]["schema"]["type"]]
                            elif 'oneOf' in process["inputs"][param]["schema"].keys(): #simple schema
                                isComplex = True
                                paramFormats = ""
                                for format in process["inputs"][param]["schema"]["oneOf"]:
                                    if format["type"] == "string":
                                        paramType = typeMapping["string"]
                                        paramFormats = paramFormats + ", " + format["contentMediaType"]
                                    if format["type"] == "object":
                                        paramType = typeMapping["object"]
                            else:
                                msg = "Parameter " + paramID + " of process " + toolID + " has no simple shema."
                                warnings.warn(msg, Warning)

                            #compile param
                            param = xml.etree.ElementTree.Element("param") 
                            param.set('name', paramID)
                            param.set('label', paramTitle)
                            param.set('help', paramDescription)
                            param.set('type', paramType)
                            if isComplex:
                                param.set('format', paramFormats[2:])

                            inputs.append(param)

                        #append inputs 
                        tool.append(inputs)

                        #add outputs
                        outputs = xml.etree.ElementTree.Element("outputs") 

                        for output in process["outputs"]:
                            outputName = output
                            outputLabel = process["outputs"][output]["title"]

                            #compile output
                            output = xml.etree.ElementTree.Element("data") 
                            output.set('name', outputName)
                            output.set('label', outputLabel)
                            outputs.append(output)

                        #append outputs
                        tool.append(outputs)
                        '''
                        #export tool 
    inputs.append(conditional_server)
    tool.append(inputs)
    tool.append(outputs)
    tree = ET.ElementTree(tool) 
    with open ("generic.xml", "wb") as toolFile: 
        ET.indent(tree, space="\t", level=0)
        tree.write(toolFile) 
    print("--> generic.xml exported")
                        

if __name__ == "__main__":
    configFile = " ".join( sys.argv[1:] )
    OGCAPIProcesses2Galaxy(configFile)
    