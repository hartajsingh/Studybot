import pandas as pd
from rdflib import Namespace, Graph, RDF, RDFS, URIRef, Literal
from rdflib.namespace import FOAF, DCTERMS, OWL, XSD
import spotlight

# create namespaces
ex = Namespace("http://example.org/")
dbo = Namespace("https://dbpedia.org/ontology/")
dbr = Namespace("https://dbpedia.org/resource/")
dbp = Namespace("https://dbpedia.org/property/")
teach = Namespace("http://linkedscience.org/teach/ns#")


# create graph and namespace bindings
graph = Graph()
graph.bind('dbo', dbo)
graph.bind('dbr', dbr)
graph.bind('dbp', dbp)
graph.bind('ex', ex)
graph.bind('teach', teach)



# load vocabulary
graph.parse('Vocabulary/RdfSchema.ttl', format='ttl')


# add concordia university
def add_university():
    graph.add((ex.Concordia_University, RDF.type , dbo.University))
    graph.add((ex.Concordia_University, dbp.name, Literal("Concordia University", lang="en")))
    graph.add((ex.Concordia_University, OWL.sameAs, URIRef(dbr.Concordia_University)))
    graph.add((ex.Concordia_University, FOAF.page , URIRef("https://dbpedia.org/resource/Concordia_University")))
    

# add course properties to graph
def add_course_properties(course_uri, course_info):
    course_name = course_info['Long Title']
    course_subject = course_info['Subject']
    course_number = course_info['Catalog']
    course_description = course_info['Descr']
    graph.add((course_uri, teach.courseTitle, Literal(course_name)))
    graph.add((course_uri, DCTERMS.subject, Literal(course_subject)))
    graph.add((course_uri, DCTERMS.identifier, Literal(course_number, datatype=XSD.integer)))
    graph.add((course_uri, teach.courseDescription, Literal(course_description, lang="en")))
  
    
# get annotated topics
def get_topics(content):
    annotations = spotlight.annotate('http://localhost:2222/rest/annotate', content, confidence=0.9, support=30)
    topic = {}
    for temp in annotations:
        topic[temp['surfaceForm'].lower()] = temp['URI']
    return topic

      
# add lecture properties to graph       
def add_lecture_properties(lecture_uri, lecture_info, course_uri, courseId):
    lecture_name = lecture_info['Name'] 
    lecture_number = lecture_info['Number']
    lecture_slides = lecture_info['Slides']
    lecture_worksheet = lecture_info['Worksheet']
    
    lecture_lab = int(lecture_info['Link'])
    lecture_lab = ex[str(lecture_lab) + '/']
        
    lecture_reading = lecture_info['Readings']
    if lecture_reading != 0:
        lecture_reading = lecture_reading.split(",")
        for reading in lecture_reading:
            reading = reading.strip()
            graph.add((URIRef(reading), RDF.type, ex.Reading))
            graph.add((URIRef(reading), RDF.type, ex.Content))
            graph.add((lecture_uri, ex.hasReading, URIRef(reading)))
            graph.add((lecture_uri, ex.hasContent, URIRef(reading)))
            
    lecture_other_material = lecture_info['Other Material']
    if lecture_other_material != 0:
        lecture_other_material = lecture_other_material.split(",")
        for material in lecture_other_material:
            material = material.strip()
            graph.add((URIRef(material), RDF.type, ex.OtherMaterial))
            graph.add((URIRef(material), RDF.type, ex.Content))
            graph.add((lecture_uri, ex.hasOtherMaterial, URIRef(material)))
            graph.add((lecture_uri, ex.hasContent, URIRef(material)))
     
    graph.add((lecture_uri, DCTERMS.title, Literal(lecture_name, lang="en")))
    graph.add((lecture_uri, DCTERMS.identifier, Literal(lecture_number, datatype=XSD.integer)))
    event = "Lecture " + str(lecture_number)
    graph.add((lecture_uri, ex.event, Literal(event, lang="en")))
    graph.add((URIRef(lecture_slides), RDF.type, ex.Slide))
    graph.add((URIRef(lecture_slides), RDF.type, ex.Content))
    graph.add((lecture_uri, ex.hasSlide, URIRef(lecture_slides)))
    graph.add((lecture_uri, ex.hasContent, URIRef(lecture_slides)))
    if lecture_number != 1:
        graph.add((URIRef(lecture_worksheet), RDF.type, ex.Worksheet))
        graph.add((URIRef(lecture_worksheet), RDF.type, ex.Content))
        graph.add((lecture_uri, ex.hasWorksheet, URIRef(lecture_worksheet)))
        graph.add((lecture_uri, ex.hasContent, URIRef(lecture_worksheet)))
    graph.add((lecture_uri, ex.hasLab, lecture_lab))
    
    # adding annotated topics to the graph
    slide_content = (open(lecture_info['Slide Path'], mode='r', encoding='utf-8')).read()
    slide_topics = get_topics(slide_content)
    for key in slide_topics:
        temp = key
        temp = temp.strip().lower().replace("\"", "").replace(" ", "")
        topic_uri = ex[str(temp) + '/' + courseId + '/']
        graph.add((topic_uri, RDF.type, ex.Topic))
        graph.add((topic_uri, DCTERMS.title, Literal(key, lang="en")))
        graph.add((topic_uri, FOAF.page, URIRef(slide_topics[key])))
        graph.add((URIRef(lecture_slides), ex.topicCovered, topic_uri))
        resource = "Slides"
        graph.add((URIRef(lecture_slides), ex.resource, Literal(resource, lang="en")))
        graph.add((course_uri, ex.hasTopic, topic_uri))
        
    if(lecture_info['Worksheet Path'] != 0):
        worksheet_content = (open(lecture_info['Worksheet Path'], mode='r', encoding='utf-8')).read()
        worksheet_topics = get_topics(worksheet_content)
        for key in worksheet_topics:
            temp = key
            temp = temp.strip().lower().replace("\"", "").replace(" ", "")
            topic_uri = ex[str(temp) + '/' + courseId + '/']
            graph.add((topic_uri, RDF.type, ex.Topic))
            graph.add((topic_uri, DCTERMS.title, Literal(key, lang="en")))
            graph.add((topic_uri, FOAF.page, URIRef(worksheet_topics[key])))
            graph.add((URIRef(lecture_worksheet), ex.topicCovered, topic_uri))
            resource = "Worksheet"
            graph.add((URIRef(lecture_worksheet), ex.resource, Literal(resource, lang="en")))
            graph.add((course_uri, ex.hasTopic, topic_uri))
          
 
# add lab properties
def add_lab_properties(lab_uri, lab_info, course_uri, courseId):
    lab_name = lab_info['Name']
    lab_number = lab_info['Number']
    lab_slides = lab_info['Slides']
    graph.add((lab_uri, DCTERMS.title, Literal(lab_name, lang="en")))
    graph.add((lab_uri, DCTERMS.identifier, Literal(lab_number, datatype=XSD.integer)))
    event = "Lab " + str(lab_number)
    graph.add((lab_uri, ex.event, Literal(event, lang="en")))
    graph.add((URIRef(lab_slides), RDF.type, ex.Slide))
    graph.add((URIRef(lab_slides), RDF.type, ex.Content))
    graph.add((lab_uri, ex.hasContent, URIRef(lab_slides)))
    graph.add((lab_uri, ex.hasSlide, URIRef(lab_slides)))
    
    slide_text = open(lab_info['Slide Path'], mode='r', encoding='utf-8')
    slide_content = slide_text.read()
    slide_topics = get_topics(slide_content)
    
    for key in slide_topics:
        temp = key
        temp = temp.strip().lower().replace("\"", "").replace(" ", "")
        topic_uri = ex[str(temp) + '/' + courseId + '/']
        graph.add((topic_uri, RDF.type, ex.Topic))
        graph.add((topic_uri, DCTERMS.title, Literal(key, lang="en")))
        graph.add((topic_uri, FOAF.page, URIRef(slide_topics[key])))
        graph.add((URIRef(lab_slides), ex.topicCovered, topic_uri))
        resource = "Slides"
        graph.add((URIRef(lab_slides), ex.resource, Literal(resource, lang="en")))
        graph.add((course_uri, ex.hasTopic, topic_uri))
    

# add comp6741 and comp6721 properties        
def add_comp6741_6721(course_uri, courseId):
    course_data = pd.read_csv('Dataset/Courses.csv', encoding='utf-8')
    course_data['Readings'] = course_data['Readings'].fillna(0)
    course_data['Other Material'] = course_data['Other Material'].fillna(0)
    course_data['Worksheet Path'] = course_data['Worksheet Path'].fillna(0)
    course_data = course_data.loc[course_data['Course'] == courseId]
    lectures = course_data.loc[course_data['Type'] == 'Lecture']
    labs = course_data.loc[course_data['Type'] == 'Lab']
    lecture_keys = lectures['Key'].values.tolist()
    lab_keys = labs['Key'].values.tolist()
    count = 0
    for lecture in lecture_keys:
        lecture_uri = ex[str(lecture) + '/']
        graph.add((lecture_uri, RDF.type, teach.Lecture))
        graph.add((course_uri, ex.hasLecture, lecture_uri))
        lecture_info = lectures.iloc[count]
        add_lecture_properties(lecture_uri, lecture_info, course_uri, courseId)
        count = count + 1
    count = 0
    for lab in lab_keys:
        lab_uri = ex[str(lab) + '/']
        graph.add((lab_uri, RDF.type, ex.Lab))
        lab_info = labs.iloc[count]
        add_lab_properties(lab_uri, lab_info, course_uri, courseId)
        count = count + 1
        
    
    
# add courses from dataset
def add_courses():
    courses_catalog = pd.read_csv('Dataset/CU_SR_OPEN_DATA_CATALOG.csv', encoding='cp1252')
    courses_catalog.drop_duplicates(subset='Course ID', inplace=True)
    courses_desc = pd.read_csv('Dataset/CU_SR_OPEN_DATA_CATALOG_DESC.csv', encoding='cp1252')
    courses = courses_catalog.merge(courses_desc, on='Course ID')
    course_keys = courses['Course ID'].values.tolist()
    count = 0
    for course in course_keys:
        course_uri = ex[str(course) + '/']
        graph.add((course_uri, RDF.type, teach.Course))
        course_info = courses.iloc[count]
        add_course_properties(course_uri, course_info)
        count = count + 1
        if course == 40355 or course == 5484:
            graph.add((course_uri, ex.outline, URIRef("file:///C:/Users/Hartaj/Desktop/Study%20Bot/Dataset/COMP6741/Outline/course_outline_comp474_6741_w2021.pdf")))
            graph.add((course_uri, RDFS.seeAlso, URIRef("http://moodle.concordia.ca/moodle/course/view.php?id=132738")))
            courseId = 'COMP6741'
            add_comp6741_6721(course_uri, courseId)
        if course == 40353:
            graph.add((course_uri, ex.outline, URIRef("file:///C:/Users/Hartaj/Desktop/Study%20Bot/Dataset/COMP6721/Outline/course_outline_comp6721_w2021.pdf")))
            graph.add((course_uri, RDFS.seeAlso, URIRef("http://moodle.concordia.ca/moodle/course/view.php?id=133697")))
            courseId = 'COMP6721'
            add_comp6741_6721(course_uri, courseId)


add_university()   
add_courses()
graph.serialize(destination='Graph/graph.nt', format='nt')