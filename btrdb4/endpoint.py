# Copyright (c) 2017 Sam Kumar <samkumar@berkeley.edu>
# Copyright (c) 2017 Michael P Andersen <m.andersen@cs.berkeley.edu>
# Copyright (c) 2017 University of California, Berkeley
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the University of California, Berkeley nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNERS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import grpc

from btrdb4 import btrdb_pb2
from btrdb4 import btrdb_pb2_grpc

from btrdb4.utils import *

class Endpoint(object):
    def __init__(self, channel):
        self.stub = btrdb_pb2_grpc.BTrDBStub(channel)

    def rawValues(self, uu, start, end, version = 0):
        params = btrdb_pb2.RawValuesParams(uuid = uu.bytes, start = start, end = end, versionMajor = version)
        for result in self.stub.RawValues(params):
            BTrDBError.checkProtoStat(result.stat)
            yield result.values, result.versionMajor

    def alignedWindows(self, uu, start, end, pointwidth, version = 0):
        params = btrdb_pb2.AlignedWindowsParams(uuid = uu.bytes, start = start, end = end, versionMajor = version, pointWidth = pointwidth)
        for result in self.stub.AlignedWindows(params):
            BTrDBError.checkProtoStat(result.stat)
            yield result.values, result.versionMajor

    def windows(self, uu, start, end, width, depth, version = 0):
        params = btrdb_pb2.WindowsParams(uuid = uu.bytes, start = start, end = end, versionMajor = version, width = width, depth = depth)
        for result in self.stub.Windows(params):
            BTrDBError.checkProtoStat(result.stat)
            yield result.values, result.versionMajor

    def streamInfo(self, uu, omitDescriptor, omitVersion):
        params = btrdb_pb2.StreamInfoParams(uuid = uu.bytes, omitVersion = omitVersion, omitDescriptor = omitDescriptor)
        result = self.stub.StreamInfo(params)
        desc = result.descriptor
        BTrDBError.checkProtoStat(result.stat)
        tagsanns = unpackProtoStreamDescriptor(desc)
        return desc.collection, desc.annotationVersion, tagsanns[0], tagsanns[1], result.versionMajor

    def setStreamAnnotations(self, uu, expected, changes):
        annkvlist = []
        for k, v in changes.items():
            if v is None:
                ov = None
            else:
                if isinstance(v, str):
                    v = v.encode("utf-8")
                ov = btrdb_pb2.OptValue(value = v)
            kv = btrdb_pb2.KeyOptValue(key = k, val = ov)
            annkvlist.append(kv)
        params = btrdb_pb2.SetStreamAnnotationsParams(uuid = uu.bytes, expectedAnnotationVersion = expected, annotations = annkvlist)
        result = self.stub.SetStreamAnnotations(params)
        BTrDBError.checkProtoStat(result.stat)

    def create(self, uu, collection, tags, annotations):
        tagkvlist = []
        for k, v in tags.items():
            kv = btrdb_pb2.KeyValue(key = k, value = v)
            tagkvlist.append(kv)
        annkvlist = []
        for k, v in annotations.items():
            kv = btrdb_pb2.KeyValue(key = k, value = v)
            annkvlist.append(kv)
        params = btrdb_pb2.CreateParams(uuid = uu.bytes, collection = collection, tags = tagkvlist, annotations = annkvlist)
        result = self.stub.Create(params)
        BTrDBError.checkProtoStat(result.stat)

    def listCollections(self, prefix, startingAt, limit):
        params = btrdb_pb2.ListCollectionsParams(prefix = prefix, startWith = startingAt, limit = limit)
        result = self.stub.ListCollections(params)
        BTrDBError.checkProtoStat(result.stat)
        return result.collections

    def lookupStreams(self, collection, isCollectionPrefix, tags, annotations):
        tagkvlist = []
        for k, v in tags.items():
            if v is None:
                ov = None
            else:
                if isinstance(v, str):
                    v = v.encode("utf-8")
                ov = btrdb_pb2.OptValue(value = v)
            kv = btrdb_pb2.KeyOptValue(key = k, val = ov)
            tagkvlist.append(kv)
        annkvlist = []
        for k, v in annotations.items():
            if v is None:
                ov = None
            else:
                if isinstance(v, str):
                    v = v.encode("utf-8")
                ov = btrdb_pb2.OptValue(value = v)
            kv = btrdb_pb2.KeyOptValue(key = k, val = ov)
            annkvlist.append(kv)
        params = btrdb_pb2.LookupStreamsParams(collection = collection, isCollectionPrefix = isCollectionPrefix, tags = tagkvlist, annotations = annkvlist)
        for result in self.stub.LookupStreams(params):
            BTrDBError.checkProtoStat(result.stat)
            yield result.results

    def nearest(self, uu, time, version, backward):
        params = btrdb_pb2.NearestParams(uuid = uu.bytes, time = time, versionMajor = version, backward = backward)
        result = self.stub.Nearest(params)
        BTrDBError.checkProtoStat(result.stat)
        return result.value, result.versionMajor

    def changes(self, uu, fromVersion, toVersion, resolution):
        params = btrdb_pb2.ChangesParams(uuid = uu.bytes, fromMajor = fromVersion, toMajor = toVersion, resolution = resolution)
        for result in self.stub.Changes(params):
            BTrDBError.checkProtoStat(result.stat)
            yield result.ranges, result.versionMajor

    def insert(self, uu, values):
        protoValues = RawPoint.toProtoList(values)
        params = btrdb_pb2.InsertParams(uuid = uu.bytes, sync = False, values = protoValues)
        result = self.stub.Insert(params)
        BTrDBError.checkProtoStat(result.stat)
        return result.versionMajor

    def deleteRange(self, uu, start, end):
        params = btrdb_pb2.DeleteParams(uuid = uu.bytes, start = start, end = end)
        result = self.stub.Delete(params)
        BTrDBError.checkProtoStat(result.stat)
        return result.versionMajor

    def info(self):
        params = btrdb_pb2.InfoParams()
        result = self.stub.Info(params)
        BTrDBError.checkProtoStat(result.stat)
        return result.mash

    def faultInject(self, typ, args):
        params = btrdb_pb2.FaultInjectParams(type = typ, params = args)
        result = self.stub.FaultInject(params)
        BTrDBError.checkProtoStat(result.stat)
        return result.rv

    def flush(self, uu):
        params = btrdb_pb2.FlushParams(uuid = uu.bytes)
        result = self.stub.Flush(params)
        BTrDBError.checkProtoStat(result.stat)
