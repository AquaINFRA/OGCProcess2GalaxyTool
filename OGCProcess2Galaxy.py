import json
import xml

def loadProcessDescription(processDescriptionFile: str) -> dict:
    try:
        with open(processDescriptionFile) as processDescriptionFile:
          processDescription = processDescriptionFile.read()
          parsedProcessDescription = json.loads(processDescription)
          
          #print(parsedProcessDescription)
          
        return parsedProcessDescription
    
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)
        else:
            print(e)
        
def validateProcessDescription(parsedProcessDescription: dict) -> bool:
    return True

def convertProcessDescription2GalaxyTool(parsedProcessDescription: dict):
    toolID = parsedProcessDescription["id"]
    toolName = parsedProcessDescription["title"]
    toolVersion = parsedProcessDescription["version"]
    
    #add tool
    tool = xml.etree.ElementTree.Element("tool") 
    tool.set('id', toolID)
    tool.set('name', toolName)
    tool.set('version', toolVersion)
    #toolTag.set('profile','Completed') ???
    
    #add description
    description = xml.etree.ElementTree.Element("description") 
    description.text = parsedProcessDescription["description"]
    tool.append(description) 
    
    #add inputs
    inputs = xml.etree.ElementTree.Element("inputs") 
    
    
    #add params
    for param in parsedProcessDescription["inputs"]:
        parsedParam = parsedProcessDescription["inputs"][param]
        
        paramName = str(param)
        paramLabel = parsedParam["title"]
        paramType = parsedParam["schema"]["type"]
        paramHelp = parsedParam["description"]
        
        
        param = xml.etree.ElementTree.Element("param") 
        param.set('name', paramName)
        param.set('label', paramLabel)
        param.set('help', paramHelp)
        param.set('type', paramType)
        inputs.append(param)
        
    tool.append(inputs)
    
    tree = xml.etree.ElementTree.ElementTree(tool) 
    
    with open (toolID + ".xml", "wb") as toolFile: 
        tree.write(toolFile) 

def convert(processDescriptionFile: str):
    parsedProcessDescription = loadProcessDescription(processDescriptionFile)
    
    valid = validateProcessDescription(parsedProcessDescription)
    
    if valid:
        convertProcessDescription2GalaxyTool(parsedProcessDescription)
    else:
        print("I am Error")

echo = convert("echo.json")