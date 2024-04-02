import json
import xml.etree.ElementTree
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
    
    #load config
    with open(configFile) as configFile:
        configJSON = json.load(configFile)

    for api in configJSON: 

        #check conformance
        with urllib.request.urlopen(api["server_url"] + "conformance") as conformanceURL:
            conformanceData = json.load(conformanceURL)
            
            for confClass in confClasses:
                if confClass not in confClasses:
                    msg = "Specified API available via:" + baseURL + " does not conform to " + confClass + "." + "This may lead to issues when converting its processes to Galaxy tools."
                    warnings.warn(msg, Warning)
        
        #get processes
        with urllib.request.urlopen(api["server_url"] + "processes") as processesURL:
            processesData = json.load(processesURL)
            
            for process in processesData["processes"]:
                if len(processesData["processes"]) == 0:
                    msg = "Specified API available via:" + baseURL + " does not provide any processes."
                    warnings.warn(msg, Warning)


                with urllib.request.urlopen(api["server_url"] + "processes/" + process["id"]) as processURL:
                    
                    process = json.load(processURL)

                    if(process["id"] in api["excluded_services"]):
                        continue

                    if(process["id"] in api["included_services"] or ("*" in api["included_services"] and len(api["included_services"]) == 1)):

                        toolID = process["id"]
                        toolName = process["title"]
                        toolVersion = process["version"]
                
                        isComplex = False

                        #add tool
                        tool = xml.etree.ElementTree.Element("tool") 
                        tool.set('id', toolID)
                        tool.set('name', toolName)
                        tool.set('version', toolVersion)
                
                        #add description
                        description = xml.etree.ElementTree.Element("description") 
                        description.text = str(process["description"])
                        tool.append(description) 
                
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

                        #export tool 
                        tree = xml.etree.ElementTree.ElementTree(tool) 
                        with open ("Output/" + toolID + ".xml", "wb") as toolFile: 
                            tree.write(toolFile) 
                        print("--> " + toolID + " exported")

if __name__ == "__main__":
    configFile = " ".join( sys.argv[1:] )
    OGCAPIProcesses2Galaxy(configFile)
    