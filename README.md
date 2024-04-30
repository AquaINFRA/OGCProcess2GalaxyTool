# Integrating OGC API Processes into Galaxy 

This tool generates a Galaxy tool that wraps OGC API Processes. The tool requests all processes hosted on the server defined in the config.json. Then, for each process, the tool requests the process description and generates the input parameters, output parameters, and commands. Processes can be excluded or picked individually using the corresponding fields in the config.json.

Some things to note:

- The XML is getting extremely large. We looked for repetitive patterns which can be replaced using macros. However, at the moment, this requires some manual work after the XML is generated. To do so, search for

  `<option value="uint8">uint8</option>
      <option value="uint16">uint16</option>
      <option value="int16">int16</option>
      <option value="int32">int32</option>
      <option value="float">float</option>
      <option value="double">double</option>` 
in the XML document and replace this section with `<expand macro="out_options"/>`

- another opportunity to reduce the XML is size is to search for

  `<option value="image/tiff">image/tiff</option>
      <option value="image/jpeg">image/jpeg</option>
      <option value="image/png">image/png</option>` 
and replace it with `<expand macro="format_options"/>`
