from pyramid.view import view_config
from pyramid.response import Response
import colander
import deform

from deform.interfaces import FileUploadTempStore

try:
    import simplejson as json
except ImportError:
    import json
import utils

#@view_config(route_name='home', renderer='templates/mytemplate.pt')
#def my_view(request):
#    return {'project':'pyrasims'}


tmpstore = FileUploadTempStore()

class SimServerInteraction(colander.MappingSchema):

    action = colander.SchemaNode(colander.String(),
            validator=colander.OneOf(['train','index','query']),
            title = 'Choose action',
            description = 'Simserver action to perform',
            default = 'query',
            missing = 'query',
            widget = deform.widget.RadioChoiceWidget(
                    values=(('query','Query'),
                        ('train','Train'),
                        ('index','Index'))
                    ))

    format = colander.SchemaNode(colander.String(),
            validator=colander.OneOf(['json','html']),
            title = 'Return Format',
            default = 'html',
            missing = 'json',
            description = 'JSON/HTML',
            widget = deform.widget.RadioChoiceWidget(
                    values=(('json','JSON'),
                        ('html','HTML'))
                    ))


    filedata = colander.SchemaNode(
            deform.FileData(),
            title = 'Upload File',
            description = 'File with documents to index or train',
            missing = '',
            widget=deform.widget.FileUploadWidget(tmpstore)
            )

    text = colander.SchemaNode(colander.String(),
            title = 'Text',
            description = 'Input text to process',
            missing = '',
            widget=deform.widget.TextAreaWidget())

    min_score = colander.SchemaNode(colander.Float(),
                validator = colander.Range(0, 1),
                missing=0,
                default = 0.5)



    max_results= colander.SchemaNode(colander.Int(),
                validator = colander.Range(0, 200),
                title = 'Max Results',
                missing = 0,
                default = 100)

class ProjectorViews(object):
    def __init__(self, request):
        self.request = request

    @view_config(route_name='home', renderer="templates/interaction_view.pt")
    def site_view(self):
        schema = SimServerInteraction()
        myform = deform.Form(schema, buttons=('submit','cancel'))
        result = None
        error = None
        data = None
        #settings = self.request.registry.settings
        print 'ProjectorViews'
        if 'submit' in self.request.POST:
            controls = self.request.POST.items()
            try:
                appstruct = myform.validate(controls)
            except deform.ValidationFailure, e:
                error = e.render()
            if appstruct['action'] == 'query':
                if appstruct['text']:
                    data = appstruct['text']
                    min_score = appstruct['min_score']
                    max_results = appstruct['max_results']
                    result = utils.find_similar(data, min_score, max_results)
                    if not result:
                        self.request.response.status = '404 Not Found'
                    if appstruct['format'] == 'json':
                        self.request.response.content_type='application/json'
                        response =  Response(json.dumps(result))
                        response.content_type='application/json'
                        return response
                else:
                    error = "No data supplied"
            elif appstruct['action'] in ['train', 'index']:
                if appstruct['text']:
                    try:
                        data = json.loads(appstruct['text'])
                    except ValueError:
                        error = "Not valid json"
                elif appstruct['filedata']:
                    afile = appstruct['filedata']['fp']
                    data = utils.extract_from_archive(afile)
                else:
                    error = "No data supplied"
                if data:
                    if appstruct['action'] == 'train':
                        result = utils.train(data)
                    elif appstruct['action'] == 'index':
                        result = utils.index(data)
        if self.request.GET:
            controls = self.request.GET.items()
            try:
                appstruct = myform.validate(controls)
            except deform.ValidationFailure, e:
                error = e.render()
            if appstruct['action'] == 'query':
               if appstruct['text']:
                    data = appstruct['text']
                    min_score = appstruct['min_score']
                    max_results = appstruct['max_results']
                    result = utils.find_similar(data, min_score, max_results)
            else:
                import ipdb; ipdb.set_trace()



        return {"error": error, "result": result, "form": myform.render()}