// XrefExporter.java
// Ghidra script to export cross-references to JSON
// Usage: analyzeHeadless ... -postScript XrefExporter.java <output_dir>

import java.io.*;
import java.util.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.ref.*;

public class XrefExporter extends GhidraScript {

    @Override
    public void run() throws Exception {
        String outputDir = getScriptArgs().length > 0 ? getScriptArgs()[0] : ".";
        String outputFile = outputDir + "/xrefs.json";

        FileWriter writer = new FileWriter(outputFile);
        writer.write("[\n");

        boolean first = true;

        // Iterate all addresses
        AddressFactory addrFactory = currentProgram.getAddressFactory();
        AddressSet allAddresses = currentProgram.getMemory().getLoadedAndInitializedAddressSet();
        AddressIterator iter = allAddresses.getAddresses(true);

        while (iter.hasNext()) {
            Address addr = iter.next();

            try {
                // Get references from this address
                ReferenceManager refMgr = currentProgram.getReferenceManager();
                Reference[] refs = refMgr.getReferencesFrom(addr);

                for (Reference ref : refs) {
                    if (ref == null) continue;

                    if (!first) writer.write(",\n");
                    first = false;

                    Address fromAddr = ref.getFromAddress();
                    Address toAddr = ref.getToAddress();
                    int type = ref.getReferenceType().getValue();
                    String typeName = ref.getReferenceType().toString();
                    boolean isCode = ref.isExternalReference() ? false : true;

                    writer.write("  {\n");
                    writer.write("    \"from_address\": \"" + fromAddr.toString() + "\",\n");
                    writer.write("    \"to_address\": \"" + toAddr.toString() + "\",\n");
                    writer.write("    \"type\": \"" + escapeJson(typeName) + "\",\n");
                    writer.write("    \"type_code\": " + type + ",\n");
                    writer.write("    \"is_code\": " + isCode + "\n");
                    writer.write("  }");
                }
            } catch (Exception e) {
                // Skip problematic addresses
            }
        }

        writer.write("\n]");
        writer.close();

        println("Cross-references exported to: " + outputFile);
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
