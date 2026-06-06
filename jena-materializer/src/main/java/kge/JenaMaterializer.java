package kge;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import java.net.URLEncoder;

import org.apache.jena.rdf.model.InfModel;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.rdf.model.Property;
import org.apache.jena.rdf.model.RDFNode;
import org.apache.jena.rdf.model.ResIterator;
import org.apache.jena.rdf.model.Resource;
import org.apache.jena.rdf.model.Statement;
import org.apache.jena.rdf.model.StmtIterator;
import org.apache.jena.reasoner.Reasoner;
import org.apache.jena.reasoner.ReasonerRegistry;
import org.apache.jena.vocabulary.RDF;
import org.apache.jena.vocabulary.RDFS;
import org.apache.jena.vocabulary.OWL;

public class JenaMaterializer {
    private static final String KGE = "urn:kge:";
    private static final String OWL_NS = "http://www.w3.org/2002/07/owl#";

    public static void main(String[] args) throws Exception {
        if (args.length != 3) {
            System.err.println(
                "Usage: mvn exec:java -Dexec.args=\"<data_path> <ontology.ttl> <output_dir>\""
            );
            System.exit(2);
        }

        Path dataPath = Path.of(args[0]);
        Path ontologyPath = Path.of(args[1]);
        Path outputPath = Path.of(args[2]);
        Files.createDirectories(outputPath);

        Map<String, Resource> entities = loadResources(
            dataPath.resolve("entities.dict"), "entity"
        );
        Map<String, Resource> relations = loadResources(
            dataPath.resolve("relations.dict"), "relation"
        );

        Model schema = ModelFactory.createDefaultModel();
        schema.read(ontologyPath.toUri().toString());
        addLabels(schema, entities);
        addLabels(schema, relations);

        Model graph = ModelFactory.createDefaultModel();
        addLabels(graph, entities);
        addLabels(graph, relations);
        loadTrainTriples(
            dataPath.resolve("train.txt"), graph, entities, relations
        );

        Model union = ModelFactory.createUnion(schema, graph);
        Reasoner reasoner = ReasonerRegistry.getOWLReasoner().bindSchema(schema);
        InfModel inferred = ModelFactory.createInfModel(reasoner, union);

        writeEntityTypes(outputPath.resolve("entity_types.tsv"), inferred, entities);
        writeRelationClasses(
            outputPath.resolve("relation_domain.tsv"),
            inferred,
            relations,
            RDFS.domain
        );
        writeRelationClasses(
            outputPath.resolve("relation_range.tsv"),
            inferred,
            relations,
            RDFS.range
        );
        writeDisjointClasses(outputPath.resolve("disjoint_classes.tsv"), inferred);
        writeFunctionalRelations(
            outputPath.resolve("functional_relations.tsv"),
            inferred,
            relations,
            "FunctionalProperty"
        );
        writeFunctionalRelations(
            outputPath.resolve("inverse_functional_relations.tsv"),
            inferred,
            relations,
            "InverseFunctionalProperty"
        );
        writeFunctionalRelations(
            outputPath.resolve("irreflexive_relations.tsv"),
            inferred,
            relations,
            "IrreflexiveProperty"
        );
    }

    private static Map<String, Resource> loadResources(Path path, String type)
            throws IOException {
        Map<String, Resource> result = new LinkedHashMap<>();
        try (BufferedReader reader = Files.newBufferedReader(
                path, StandardCharsets.UTF_8)) {
            String line;
            while ((line = reader.readLine()) != null) {
                String[] parts = line.split("\t", 2);
                String name = parts[1];
                result.put(name, resource(type, name));
            }
        }
        return result;
    }

    private static void loadTrainTriples(
            Path path,
            Model graph,
            Map<String, Resource> entities,
            Map<String, Resource> relations) throws IOException {
        try (BufferedReader reader = Files.newBufferedReader(
                path, StandardCharsets.UTF_8)) {
            String line;
            while ((line = reader.readLine()) != null) {
                String[] parts = line.split("\t", 3);
                graph.add(
                    entities.get(parts[0]),
                    graph.createProperty(relations.get(parts[1]).getURI()),
                    entities.get(parts[2])
                );
            }
        }
    }

    private static void addLabels(Model model, Map<String, Resource> resources) {
        for (Map.Entry<String, Resource> entry : resources.entrySet()) {
            model.add(entry.getValue(), RDFS.label, entry.getKey());
        }
    }

    private static Resource resource(String type, String name) {
        return ModelFactory.createDefaultModel().createResource(
            KGE + type + ":" + URLEncoder.encode(
                name, StandardCharsets.UTF_8
            ).replace("+", "%20")
        );
    }

    private static void writeEntityTypes(
            Path path,
            InfModel model,
            Map<String, Resource> entities) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(
                path, StandardCharsets.UTF_8)) {
            for (Map.Entry<String, Resource> entry : entities.entrySet()) {
                StmtIterator types = model.listStatements(
                    entry.getValue(), RDF.type, (RDFNode) null
                );
                TreeSet<String> classUris = new TreeSet<>();
                while (types.hasNext()) {
                    RDFNode type = types.nextStatement().getObject();
                    if (type.isURIResource()) {
                        classUris.add(type.asResource().getURI());
                    }
                }
                for (String classUri : classUris) {
                    writer.write(entry.getKey());
                    writer.write('\t');
                    writer.write(classUri);
                    writer.newLine();
                }
            }
        }
    }

    private static void writeRelationClasses(
            Path path,
            InfModel model,
            Map<String, Resource> relations,
            Property property) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(
                path, StandardCharsets.UTF_8)) {
            for (Map.Entry<String, Resource> entry : relations.entrySet()) {
                StmtIterator statements = model.listStatements(
                    entry.getValue(), property, (RDFNode) null
                );
                TreeSet<String> classUris = new TreeSet<>();
                while (statements.hasNext()) {
                    RDFNode node = statements.nextStatement().getObject();
                    if (node.isURIResource()) {
                        classUris.add(node.asResource().getURI());
                    }
                }
                for (String classUri : classUris) {
                    writer.write(entry.getKey());
                    writer.write('\t');
                    writer.write(classUri);
                    writer.newLine();
                }
            }
        }
    }

    private static void writeDisjointClasses(Path path, InfModel model)
            throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(
                path, StandardCharsets.UTF_8)) {
            StmtIterator statements = model.listStatements(
                null, OWL.disjointWith, (RDFNode) null
            );
            TreeSet<String> pairs = new TreeSet<>();
            while (statements.hasNext()) {
                Statement statement = statements.nextStatement();
                if (statement.getSubject().isURIResource()
                        && statement.getObject().isURIResource()) {
                    String first = statement.getSubject().getURI();
                    String second = statement.getObject().asResource().getURI();
                    if (isUserClass(first) && isUserClass(second)) {
                        pairs.add(first + "\t" + second);
                    }
                }
            }
            addComplementPairs(model, pairs);
            addAllDisjointClassPairs(model, pairs);
            for (String pair : pairs) {
                writer.write(pair);
                writer.newLine();
            }
        }
    }

    private static void addComplementPairs(Model model, TreeSet<String> pairs) {
        Property complementOf = model.createProperty(OWL_NS + "complementOf");
        StmtIterator statements = model.listStatements(
            null, complementOf, (RDFNode) null
        );
        while (statements.hasNext()) {
            Statement statement = statements.nextStatement();
            if (statement.getSubject().isURIResource()
                    && statement.getObject().isURIResource()) {
                String first = statement.getSubject().getURI();
                String second = statement.getObject().asResource().getURI();
                if (isUserClass(first) && isUserClass(second)) {
                    pairs.add(first + "\t" + second);
                }
            }
        }
    }

    private static void addAllDisjointClassPairs(Model model, TreeSet<String> pairs) {
        Resource allDisjointClasses = model.createResource(
            OWL_NS + "AllDisjointClasses"
        );
        Property members = model.createProperty(OWL_NS + "members");
        ResIterator resources = model.listResourcesWithProperty(
            RDF.type, allDisjointClasses
        );
        while (resources.hasNext()) {
            Resource disjointSet = resources.nextResource();
            StmtIterator statements = model.listStatements(
                disjointSet, members, (RDFNode) null
            );
            while (statements.hasNext()) {
                RDFNode listNode = statements.nextStatement().getObject();
                TreeSet<String> classUris = readRdfList(model, listNode);
                for (String first : classUris) {
                    for (String second : classUris) {
                        if (!first.equals(second)) {
                            if (isUserClass(first) && isUserClass(second)) {
                                pairs.add(first + "\t" + second);
                            }
                        }
                    }
                }
            }
        }
    }

    private static TreeSet<String> readRdfList(Model model, RDFNode listNode) {
        TreeSet<String> classUris = new TreeSet<>();
        RDFNode current = listNode;
        while (current != null
                && current.isResource()
                && !current.asResource().equals(RDF.nil)) {
            Resource listResource = current.asResource();
            Statement first = model.getProperty(listResource, RDF.first);
            if (first != null && first.getObject().isURIResource()) {
                classUris.add(first.getObject().asResource().getURI());
            }
            Statement rest = model.getProperty(listResource, RDF.rest);
            current = rest == null ? null : rest.getObject();
        }
        return classUris;
    }

    private static void writeFunctionalRelations(
            Path path,
            InfModel model,
            Map<String, Resource> relations,
            String propertyTypeName) throws IOException {
        Resource propertyType = model.createResource(OWL_NS + propertyTypeName);
        try (BufferedWriter writer = Files.newBufferedWriter(
                path, StandardCharsets.UTF_8)) {
            for (Map.Entry<String, Resource> entry : relations.entrySet()) {
                ResIterator resources = model.listResourcesWithProperty(
                    RDF.type, propertyType
                );
                while (resources.hasNext()) {
                    if (resources.nextResource().equals(entry.getValue())) {
                        writer.write(entry.getKey());
                        writer.newLine();
                        break;
                    }
                }
            }
        }
    }

    private static boolean isUserClass(String uri) {
        return !uri.startsWith("http://www.w3.org/2001/XMLSchema#")
            && !uri.startsWith("http://www.w3.org/2000/01/rdf-schema#")
            && !uri.startsWith("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
            && !uri.startsWith("http://www.w3.org/2002/07/owl#");
    }

}
