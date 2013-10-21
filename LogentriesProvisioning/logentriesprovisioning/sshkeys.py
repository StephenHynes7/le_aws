import os.path
from os.path import expanduser

# TODO: rename following the same convention as for the other clases
class SSHKeys:

    @staticmethod
    def expand_path(path):
        return os.path.expanduser(path)

    @staticmethod
    def expand_paths(paths):
        result = []
        for path in paths:
            expanded_path = os.path.expanduser(path)
            if expanded_path not in result:
                result.append(expanded_path)
        return result

    def __init__(self,names=None,paths=None):
        self._paths = []
        if paths is not None:
            self._paths.extend(paths)
        if names == None:
            self._names = []
        else:
            self._names = names
        self._mapping = {}

    def get_paths(self):
        """ """
        return self._paths

    def set_paths(self,paths):
        """ """
        self._paths = paths

    def get_names(self):
        """ """
        return self._names

    def set_names(self,names):
        """ """
        self._names = names

    def get_mappings(self):
        """ """
        return self._mappings

    def set_mappings(self,mappings):
        """ """
        self._mappings = mappings

    def get_path(self,name):
        """ """
        if name in self.get_mapping():
            return self.get_mapping()[name]
        return None

    def get_key_path(self,name):
        """ """
        if name in self.get_mapping():
            return '%s%s'%(self.get_mapping()[name],name)
        return None

    def set_path(self,name,path):
        """ """
        if path not in self.get_paths():
            self.get_mapping()[name] = path

    def get_key(self,name):
        """ """
        path = self.get_path(name)
        if path is not None:
            return {name:path}
        return None

    def get_key_onpath(self,path,key_name):
        """
        Args:
        key_name is the name of the key, incuding its extension, e.g. my_key.pem
        """
        clean_path = path
        if not clean_path.endswith('/'):
            clean_path = clean_path+'/' 
        key_full_path = '%s%s%s'%(clean_path,key_name,'.pem')
        if os.path.isfile(os.path.expanduser(key_full_path)):
            return key_full_path
        return None

    def get_keys_onpath(self,path,key_names):
        """ """
        result = {}
        for key_name in key_names:
            key_path = self.get_key_onpath(path,key_name)
            if key_path is not None and key_path not in result:
                result[key_name] = key_path
        return result


    def get_keys_onpaths(self,paths,key_names):
        """ """
        result = {}
        for path in paths:
            result.update(self.get_keys_onpath(path,key_names))
        return result


