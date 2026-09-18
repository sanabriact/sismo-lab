class AssociationManager:
    def __init__(self):
        self.W = 48.0 #horas
        self.R = 40.0 #km
        self.candidates ={} #dict int:list
        self.selected_reference = {}#dict int:int
