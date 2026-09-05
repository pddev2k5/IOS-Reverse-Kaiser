// StringExporter.java
// Ghidra script to export all strings to JSON
// Usage: analyzeHeadless ... -postScript StringExporter.java <output_dir>

import java.io.*;
import java.util.*;
import ghidra.app.script.GhidraScript;
import ghidra.app.util.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.data.*;

public class StringExporter extends GhidraScript {

    @Override
    public void run() throws Exception {
        String outputDir = getScriptArgs().length > 0 ? getScriptArgs()[0] : ".";
        String outputFile = outputDir + "/strings.json";

        FileWriter writer = new FileWriter(outputFile);
        writer.write("[\n");

        boolean first = true;

        // Get all defined data
        DataIterator dataIter = currentProgram.getListing().getDefinedData(true);

        while (dataIter.hasNext()) {
            Data data = dataIter.next();

            try {
                // Check if it's a string
                if (isString(data)) {
                    String stringValue = getStringValue(data);
                    if (stringValue != null && stringValue.length() >= 4) {
                        Address addr = data.getAddress();
                        String type = data.getDataType().getName();

                        if (!first) writer.write(",\n");
                        first = false;

                        writer.write("  {\n");
                        writer.write("    \"address\": \"" + addr.toString() + "\",\n");
                        writer.write("    \"value\": \"" + escapeJson(stringValue) + "\",\n");
                        writer.write("    \"length\": " + stringValue.length() + ",\n");
                        writer.write("    \"type\": \"" + escapeJson(type) + "\"\n");
                        writer.write("  }");
                    }
                }
            } catch (Exception e) {
                // Skip problematic data
            }
        }

        writer.write("\n]");
        writer.close();

        println("Strings exported to: " + outputFile);
    }

    private boolean isString(Data data) {
        DataType dt = data.getDataType();
        String typeName = dt.getName().toLowerCase();
        return typeName.contains("string") ||
               typeName.contains("char") ||
               typeName.contains("unicode");
    }

    private String getStringValue(Data data) {
        try {
            Object obj = data.getValue();
            if (obj instanceof String) {
                return (String) obj;
            }
        } catch (Exception e) {
            // Fall back to raw bytes
        }
        return null;
    }

    private String escapeJson(String s) {
        if (s == null) return "";
        return s.replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }
}
