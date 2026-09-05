// FunctionExporter.java
// Ghidra script to export all functions to JSON
// Usage: analyzeHeadless ... -postScript FunctionExporter.java <output_dir>

import java.io.*;
import java.util.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.util.task.TaskMonitor;

public class FunctionExporter extends GhidraScript {

    @Override
    public void run() throws Exception {
        String outputDir = getScriptArgs().length > 0 ? getScriptArgs()[0] : ".";
        String outputFile = outputDir + "/functions.json";

        FileWriter writer = new FileWriter(outputFile);
        writer.write("[\n");

        FunctionManager fm = currentProgram.getFunctionManager();
        Iterator<Function> iter = fm.getFunctions(true);
        boolean first = true;

        while (iter.hasNext()) {
            Function func = iter.next();

            if (!first) writer.write(",\n");
            first = false;

            String entryPoint = func.getEntryPoint().toString();
            String name = func.getName();
            long size = func.getBody().getNumAddresses();
            String signature = func.getSignature().getPrototypeString();
            String callingConvention = func.getCallingConventionName();

            // Get local variables count
            Variable[] locals = func.getAllVariables();
            int localCount = 0;
            for (Variable v : locals) {
                if (!v.isParameter()) localCount++;
            }

            writer.write("  {\n");
            writer.write("    \"address\": \"" + entryPoint + "\",\n");
            writer.write("    \"name\": \"" + escapeJson(name) + "\",\n");
            writer.write("    \"size\": " + size + ",\n");
            writer.write("    \"signature\": \"" + escapeJson(signature) + "\",\n");
            writer.write("    \"calling_convention\": \"" + escapeJson(callingConvention) + "\",\n");
            writer.write("    \"local_variables\": " + localCount + "\n");
            writer.write("  }");
        }

        writer.write("\n]");
        writer.close();

        println("Functions exported to: " + outputFile);
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
