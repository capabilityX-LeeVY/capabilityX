import threading
from core.mac.AXClasses import NativeUIElement
from typing import Optional
import collections
from common.utils.logger import LOGGER_INFO
import hashlib

class CTraversedItem(object):
    def __init__(self,element:Optional['NativeUIElement']) -> None:
        if element is not None:
            self.controlName = element.avaliableInfo
            self.hash = element.hashstr
            self.tapOrder = element.tabOrder
            self.fromControler = element.fromControl
            self.parentHash = ""
            if element.parent is not None and isinstance(element.parent,NativeUIElement) ==True:
                self.parentHash = element.parent.hashstr
            
        self.count = 1

class CTraversedElementMgr(object):
    _instance_lock = threading.Lock()
    def __init__(self) -> None:
        pass

    def Init(self):
        self.traversedElements = collections.OrderedDict()
        self.insertFlag = False

    def __new__(cls, *args, **kwargs):
        if not hasattr(CTraversedElementMgr, "_instance"):
            with CTraversedElementMgr._instance_lock:
                if not hasattr(CTraversedElementMgr, "_instance"):
                    CTraversedElementMgr._instance = object.__new__(cls)
                    CTraversedElementMgr._instance.Init()

        return CTraversedElementMgr._instance

    def Insert2(self,item:CTraversedItem,insert = True):
        if self.insertFlag == False:
            return False
        
        if item is None:
            raise Exception("Element is None!")
        
        hashStr = f'''{item.hash}_{item.parentHash}_{item.fromControler}'''
        if item.fromControler is None:
            hashStr = f'''{item.hash}_{item.parentHash}'''
            
        hash = hashlib.sha256(hashStr.encode("utf-8")).hexdigest()[:128]
        if hash in self.traversedElements:
            if insert == True:
                traversed:CTraversedItem = self.traversedElements[hash]
                traversed.count = traversed.count + 1 
                if traversed.count >= 10:
                    msg = f'''{traversed.controlName}: duplicate item more than 10 times'''
                    raise Exception(msg)
            return True
        else:
            if insert == True:
                self.traversedElements[hash] = item
                return True
            return False
        
    def Insert(self,element:Optional['NativeUIElement'],insert = True):
        if self.insertFlag == False:
            return False
        
        if element is None:
            raise Exception("Element is None!")
        
        item = CTraversedItem(element)
        return self.Insert2(item=item,insert=insert)
        
    def IsIn(self,element:Optional['NativeUIElement']):
        return self.Insert(element,insert=False)
    

    def PrintElements(self):
        for hash in self.traversedElements:
            item:CTraversedItem = self.traversedElements[hash]
            name = item.controlName
            tapOrder = item.tapOrder
            count = item.count
            message = f'''name: {name} count: {count}  tapOrder: {tapOrder} hash:{hash}'''
            LOGGER_INFO(message)
    
    def ResetEachItemCount(self):
        for hash in self.traversedElements:
            item:CTraversedItem = self.traversedElements[hash]
            item.count = 1


class CTraversed(object):
    def __init__(self) -> None:
        pass

    @staticmethod
    def InsertElement(element:Optional['NativeUIElement']):
        mgr = CTraversedElementMgr()
        return mgr.Insert(element)

    @staticmethod

    def InsertElement2(element:CTraversedItem):
        mgr = CTraversedElementMgr()
        return mgr.Insert2(element)
    
    @staticmethod 
    def IsElementIn(element:Optional['NativeUIElement']):
        mgr = CTraversedElementMgr()
        return mgr.IsIn(element)
    
    @staticmethod 
    def PrintElements():
        mgr = CTraversedElementMgr()
        mgr.PrintElements()

    @staticmethod 
    def UpdateInsertFlag(insertFlag:bool):
        mgr = CTraversedElementMgr()
        mgr.insertFlag = insertFlag

    @staticmethod 
    def ResetEachItemCount():
        mgr = CTraversedElementMgr()
        mgr.ResetEachItemCount()