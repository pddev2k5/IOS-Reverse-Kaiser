// DecompilerExporter.java
// Ghidra script to export decompiled function pseudocode to JSON
// Usage: analyzeHeadless ... -postScript DecompilerExporter.java <output_dir> [address]

import java.io.*;
import java.util.*;
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class DecompilerExporter extends GhidraScript {

    private DecompInterface decompInterface;

    @Override
    protected void run() throws Exception {
        String outputDir = getScriptArgs().length > 0 ? getScriptArgs()[0] : ".";
        String addressStr = getScriptArgs().length > 1 ? getScriptArgs()[1] : null;

        // Initialize decompiler
        decompInterface = new DecompInterface();
        decompInterface.setOptions(this.getCurrentProgram());
        decompInterface.toggleSyntaxTree(true);
        decompInterface.setSimplificationStyle("normalize");

        FileWriter writer = null;
        String outputFile = null;

        if (addressStr != null) {
            // Export single function
            outputFile = outputDir + "/decompiled/" + addressStr.replace("0x", "") + ".json";
            new File(outputDir + "/decompiled").mkdirs();
            writer = new FileWriter(outputFile);
            writer.write("{\n");

            try {
                Address addr = getAddressFactory().getAddress(addressStr);
                Function func = getFunctionContaining(addr);

                if (func != null) {
                    exportFunction(writer, func);
                } else {
                    writer.write("  \"error\": \"Function not found at " + addressStr + "\"\n");
                }
            } catch (Exception e) {
                writer.write("  \"error\": \"" + escapeJson(e.getMessage()) + "\"\n");
            }

            writer.write("}");
            writer.close();
            println("Decompiled function exported to: " + outputFile);
        } else {
            // Export all functions
            outputFile = outputDir + "/decompiled.json";
            new File(outputDir + "/decompiled").mkdirs();
            writer = new FileWriter(outputFile);
            writer.write("[\n");

            FunctionManager fm = currentProgram.getFunctionManager();
            Iterator<Function> iter = fm.getFunctions(true);
            boolean first = true;

            while (iter.hasNext()) {
                Function func = iter.next();

                try {
                    if (!first) writer.write(",\n");
                    first = false;

                    writer.write("  {\n");
                    exportFunction(writer, func);
                    writer.write("  }");
                } catch (Exception e) {
                    if (!first) writer.write(",\n");
                    first = false;
                    writer.write("  {\n");
                    writer.write("    \"address\": \"" + func.getEntryPoint().toString() + "\",\n");
                    writer.write("    \"error\": \"" + escapeJson(e.getMessage()) + "\"\n");
                    writer.write("  }");
                }
            }

            writer.write("\n]");
            writer.close();
            println("All decompiled functions exported to: " + outputFile);
        }
    }

    private void exportFunction(FileWriter writer, Function func) throws IOException {
        String address = func.getEntryPoint().toString();
        String name = func.getName();
        String signature = func.getSignature().getPrototypeString();

        writer.write("    \"address\": \"" + address + "\",\n");
        writer.write("    \"name\": \"" + escapeJson(name) + "\",\n");
        writer.write("    \"signature\": \"" + escapeJson(signature) + "\",\n");

        // Decompile
        String pseudocode = decompile(func);
        writer.write("    \"pseudocode\": \"" + escapeJson(pseudocode) + "\",\n");

        // Get warnings
        writer.write("    \"warnings\": []\n");
    }

    private String decompile(Function func) {
        try {
            DecompileResults results = decompInterface.decompileFunction(func, 30, null);
            if (results.decompileCompleted()) {
                return results.getDecompiledFunction().getC();
            } else {
                return "// Decompilation failed: " + results.getErrorMessage();
            }
        } catch (Exception e) {
            return "// Error: " + e.getMessage();
        }
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
