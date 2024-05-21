import json
import xml.etree.ElementTree as ET
import urllib.request 
import warnings
import sys
import xml.dom.minidom as md

#OGC Process Description types to Galaxy Parameter types
typeMapping = {
  "array": "text",
  "boolean": "boolean",
  "integer": "integer",
  "number": "float",
  "object": "data",
  "string": "text"
}

mediaTypes = ["image/tiff", "image/jpeg", "image/png"]

#conformance classes 
confClasses = [
"http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core",
"http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/ogc-process-description",
"http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/json"
]

def contains_ref(json_obj):
    try:
        if isinstance(json_obj, dict):
            if "$ref" in json_obj:
                return True
            for value in json_obj.values():
                if contains_ref(value):
                    return True
        elif isinstance(json_obj, list):
            for item in json_obj:
                if contains_ref(item):
                    return True
        return False
    except:
        return False

def distinct_subarray(arr):
    subarray = []
    seen = set()
    for item in arr:
        if item not in seen:
            subarray.append(item)
            seen.add(item)
    return subarray

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

    #load config
    with open(configFile) as configFile:
        configJSON = json.load(configFile)

    #add tool
    tool = ET.Element("tool") 
    tool.set('id', configJSON["id"])
    tool.set('name', configJSON["title"])
    tool.set('version', configJSON["version"])

    #add description
    description = ET.Element("description")
    description.text = "executes remote processes"
    tool.append(description)

    #add macro
    macros = ET.Element("macros")
    importMacro = ET.Element("import")
    importMacro.text = "macros.xml"
    macros.append(importMacro)
    tool.append(macros)

    #add requirements
    requirements = ET.Element("expand")
    requirements.set("macro", "requirements")
    tool.append(requirements)

    #add command
    command = ET.Element("command")
    command.set("detect_errors", "exit_code")
    commands = []

    #add inputs
    inputs = ET.Element("inputs")

    #conditional_server = ET.Element("conditional")
    #conditional_server.set("name", "conditional_server")
    #select_server = ET.Element("param")
    #select_server.set("name", "select_server")
    #select_server.set("type", "select")
    #select_server.set("label", "Select server")

    index_i = 0
    for api in configJSON["servers"]: 
        index_i += 1
        #check conformance
        with urllib.request.urlopen(api["server_url"] + "conformance") as conformanceURL:
            conformanceData = json.load(conformanceURL)
            
            for confClass in confClasses:
                if confClass not in confClasses:
                    msg = "Specified API available via:" + api + " does not conform to " + confClass + "." + "This may lead to issues when converting its processes to Galaxy tools."
                    warnings.warn(msg, Warning)

        #server = ET.Element("option")
        #server.text = api["server_url"]
        #server.set("value", api["server_url"])
        #select_server.append(server)

        #make sure select-server dropdown is at the beginning
        #if index_i == len(configJSON):
        #    conditional_server.append(select_server)

        #when_server = ET.Element("when")
        #when_server.set("value", api["server_url"])

        conditional_process = ET.Element("conditional")
        conditional_process.set("name", "conditional_process")
        select_process = ET.Element("param")
        select_process.set("name", "select_process")
        select_process.set("type", "select")
        select_process.set("label", "Select process")

        with urllib.request.urlopen(api["server_url"] + "processes" + api["filter"]) as processesURL:
            processesData = json.load(processesURL)
            
            when_list_processes = []
            for process in processesData["processes"]: #only get 50 processes!
                
                #command information for process
                processCommand = {"server": api["server_url"], "process": process["id"]}

                #check if process is excluded
                if(process["id"] in api["excluded_services"]):
                    continue

                #check if process is included
                if(process["id"] in api["included_services"] or ("*" in api["included_services"] and len(api["included_services"]) == 1)):
                    with urllib.request.urlopen(api["server_url"] + "processes/" + process["id"]) as processURL:
                        process = json.load(processURL)
                        processElement = ET.Element("option")

                        if("title" in process.keys()):
                            processElement.text = process["id"] + ": " + process["title"]
                        else:
                            processElement.text = process["id"]  

                        processElement.set("value", process["id"])
                        select_process.append(processElement)

                        when_process = ET.Element("when")
                        when_process.set("value", process["id"])
                        
                        #inputs for commands 
                        inputCommand = []

                        #iterate over process params
                        for param in process["inputs"]:
                            inputCommand.append(param)
                            process_input = ET.Element("param")

                            #set param name
                            process_input.set("name", param) 
                            
                            #set param title
                            if "title" in process["inputs"][param].keys():
                                    process_input.set("label", process["inputs"][param]["title"])
                            else:
                                process_input.set("label", param)

                            if "nullable" in process["inputs"][param]["schema"].keys():
                                if process["inputs"][param]["schema"]["nullable"]:
                                    process_input.set("optional", "true")
                                else:
                                    process_input.set("optional", "false")

                            #set default
                            if "default" in process["inputs"][param]["schema"].keys():
                                process_input.set("value", str(process["inputs"][param]["schema"]["default"]))
                            
                            #set param description
                            if "description" in process["inputs"][param].keys():
                                process_input.set("help", process["inputs"][param]["description"])
                            else:
                                process_input.set("help", "No description provided!")

                            #set param type
                            if("extended-schema" in process["inputs"][param].keys()):
                                schema = process["inputs"][param]["extended-schema"]
                            else: 
                                schema = process["inputs"][param]["schema"]
                            
                            if 'oneOf' in schema.keys(): 
                                schema = process["inputs"][param]["schema"]["oneOf"][0]

                            if 'type' in schema.keys(): #simple schema
                                if schema["type"] in typeMapping.keys():
                                    process_input.set("type", typeMapping[schema["type"]])
                                    if "format" in schema.keys():
                                        if schema["format"] == "binary":
                                            process_input.set("type", "data")
                                    if "contentMediaType" in schema.keys():
                                        if schema["contentMediaType"] in mediaTypes:
                                            process_input.set("type", "data")
                                    if schema["type"] == "boolean":
                                        process_input.set("truevalue", "True") # Galaxy uses this for bools
                                        process_input.set("falsevalue", "False")
                                    if "enum" in schema: #create dropdown if enum exists
                                        enums = distinct_subarray(schema["enum"])
                                        process_input.set("type", "select")
                                        for enum in enums:
                                            option = ET.Element("option")
                                            option.set("value", enum)
                                            option.text = enum
                                            process_input.append(option)
                                    if schema["type"] == "array":
                                        if 'items' in schema.keys():
                                            if 'type' in schema["items"].keys():
                                                #process_input.set("type", typeMapping[schema["items"]["type"]])
                                                process_input.set("name", param +  "_Array_" + typeMapping[schema["items"]["type"]])
                                                process_input.set("type", "text")
                                                process_input.set("help", "Please provide comma-seperated values of type " + typeMapping[schema["items"]["type"]] + " here.")

                            when_process.append(process_input)
                        
                        #add inputs to command information for process
                        processCommand["inputs"] = inputCommand
                        
                        outputFormatCommands = []

                        for output in process["outputs"]:
                            outputName = output
                            processOutput = process["outputs"][output]
                            if "extended-schema" in processOutput:
                                process_output = ET.Element("param")
                                process_output.set("type", "select")
                                process_output.set("name", outputName.replace(".", "_") + "_outformat") #_out needed to avoid duplicates
                                process_output.set("label", outputName + "_outformat")
                                process_output.set("help", "Output format")
                                outputFormatCommands.append(outputName + "_outformat")
                                enums = distinct_subarray(processOutput["extended-schema"]["oneOf"][0]["allOf"][1]["properties"]["type"]["enum"])
                                for enum in enums:
                                    output_option = ET.Element("option")
                                    output_option.set("value", enum)
                                    output_option.text=enum
                                    process_output.append(output_option)
                                when_process.append(process_output)
                        processCommand["outputs"] = outputFormatCommands
                        commands.append(processCommand)
                        when_list_processes.append(when_process)

        conditional_process.append(select_process)
        for when_process in when_list_processes:
            conditional_process.append(when_process)    
        #when_server.append(conditional_process)
    #conditional_server.append(when_server)

    #add command
    commandText = "<![CDATA["
    
    #for i in range(0, len(commands)):
        #if i == 0:
            #commandText += "\n#if $conditional_server.select_process == \"" + commands[i]["process"] + "\":\n"
            #commandText += "\n#if $select_process == \"" + commands[i]["process"] + "\":\n"
    commandText += "\n\tRscript '$__tool_directory__/generic.R'\n"
            #commandText += "\t\t--server '$select_server' \n"
            #commandText += "\t\t--server " + api["server_url"] + "\n"
            #commandText += "\t\t--process '$select_process'"
            #for y in commands[i]["inputs"]:
            #    commandText += "\n\t\t--"+ y + " \'${" + y.replace(".", "_") + "}\'"
            #for o in commands[i]["outputs"]:
            #    commandText += "\n\t\t--"+ o + " \'${" + o.replace(".", "_") + "}\'"
            #commandText += "\t\t--inputs '$inputs'"
    commandText += "\t\t--outputData '$output_data'"
        #else:
            #commandText += "\n#elif $conditional_server.select_process == \"" + commands[i]["process"] + "\":\n"
            #commandText += "\n#elif $select_process == \"" + commands[i]["process"] + "\":\n"
            #commandText += "\tRscript '$__tool_directory__/generic.R'\n"
            #commandText += "\t\t--server '$select_server' \n"
            #commandText += "\t\t--server " + api["server_url"] + "\n"
            #commandText += "\t\t--process '$select_process'"
            #for y in commands[i]["inputs"]:
            #    commandText += "\n\t\t--"+ y + " \'${" + y.replace(".", "_") + "}\'"
            #for o in commands[i]["outputs"]:
            #    commandText += "\n\t\t--"+ o + " \'${" + o.replace(".", "_") + "}\'"
            #commandText += "\t\t--inputs '$inputs'"
            #commandText += "\n\t\t--outputData '$output_data'"
    commandText += "\n]]>"
    command.text = commandText
    tool.append(command)

    #add configfiles
    configfiles = ET.Element("configfiles")
    configfiles_inputs = ET.Element("inputs")
    configfiles_inputs.set("name", "inputs")
    configfiles_inputs.set("filename", "inputs.json")
    configfiles_inputs.set("data_style", "paths")
    configfiles.append(configfiles_inputs)
    tool.append(configfiles)

    #add inputs 
    #inputs.append(conditional_server)
    inputs.append(conditional_process)
    tool.append(inputs)

    #add outputs
    outputs = ET.Element("outputs")
    dataOutput = ET.Element("data")
    dataOutput.set("name", "output_data")
    dataOutput.set("format", "txt")
    dataOutput.set("label", "$select_process")
    #discover_datasets = ET.Element("discover_datasets")
    #discover_datasets.set("pattern", "__name_and_ext__")
    #collection.append(discover_datasets)
    outputs.append(dataOutput)
    tool.append(outputs)

    #add tests
    tests = ET.Element("expand")
    tests.set("macro", "tests")
    tool.append(tests)

    #add help
    help = ET.Element("expand")
    help.set("macro", "help")
    tool.append(help)

    #add citation
    citations = ET.Element("expand")
    citations.set("macro", "citations")
    tool.append(citations)

    with open ("generic.xml", "wb") as toolFile: 
        toolString = ET.tostring(tool, encoding='unicode')
        toolString = toolString.replace("&lt;", "<")
        toolString = toolString.replace("&gt;", ">")

        toolString = md.parseString(toolString)
        toolString = toolString.toprettyxml()

        f = open("generic.xml", "a")
        f.write(toolString)
        f.close()
    print("--> generic.xml exported")

if __name__ == "__main__":
    configFile = " ".join( sys.argv[1:] )
    OGCAPIProcesses2Galaxy(configFile)
    