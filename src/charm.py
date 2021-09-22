#!/usr/bin/env python3
# Copyright 2021 root
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging
import ctypes
import ctypes.util
import os 

from ops.charm import CharmBase, LeaderElectedEvent, RelationJoinedEvent , RelationDepartedEvent, RelationChangedEvent, StorageAttachedEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus


logger = logging.getLogger(__name__)

libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
libc.mount.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p)

class MinioCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.minio_list = []
        self.framework.observe(self.on.minio_pebble_ready, self.on_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        # self.framework.observe(self.on.leader_elected, self._on_leader_elected)

        self.framework.observe(self.on.replicas_relation_joined, self._on_replicas_relation_joined)
        self.framework.observe(self.on.replicas_relation_departed, self._on_replicas_relation_departed)
        self.framework.observe(self.on.replicas_relation_changed, self._on_replicas_relation_changed)

        # self.framework.observe(self.on.miniodata_storage_attached,self._on_miniodata_storage_attached)

        self._stored.set_default(leader_ip="")
        self._stored.set_default(secret_key="")
        self._stored.set_default(minio_list="")

    def _on_leader_elected(self, event: LeaderElectedEvent) -> None:
        """Handle the leader-elected event"""
        logging.debug("Leader %s setting some data!", self.unit.name)
        # Get the peer relation object
        peer_relation = self.model.get_relation("replicas")
        # Get the bind address from the juju model
        # Convert to string as relation data must always be a string
        ip = str(self.model.get_binding(peer_relation).network.bind_address)
        self.unit.status = ActiveStatus(str(ip))
        # Update some data to trigger a replicas_relation_changed event
        peer_relation.data[self.app].update({"leader-ip": ip})

    def _on_replicas_relation_joined(self, event: RelationJoinedEvent) -> None:
        """Handle relation-joined event for the replicas relation"""
        logger.debug("Hello from %s to %s", self.unit.name, event.unit.name)

        # self.unit.status = ActiveStatus(self.unit.is_leader())
        # Check if we're the leader
        # if self.unit.is_leader():
            # Get the bind address from the juju model
        ip = str(self.model.get_binding(event.relation).network.bind_address)
        logging.debug("Leader %s setting some data!", self.unit.name)
        # event.relation.data[self.app].update({"leader-ip": ip})

        # Update our unit data bucket in the relation
        event.relation.data[self.unit].update({"unit-data": self.unit.name})
    
    def _on_replicas_relation_departed(self, event: RelationDepartedEvent) -> None:
        """Handle relation-departed event for the replicas relation"""
        logger.debug("Goodbye from %s to %s", self.unit.name, event.unit.name)

    def _on_replicas_relation_changed(self, event: RelationChangedEvent) -> None:
        """Handle relation-changed event for the replicas relation"""
        # self.minio_list = []
        for keys,values in event.relation.data.items():
            logging.info(f"{keys}     {values}")
            try:
                app = keys.app
                self.minio_list.append(str(keys.name).replace("/","-"))
            except:
                pass
        self.unit.status = ActiveStatus(str(self.minio_list))

        # trigger on_config_changed event 
        self._on_config_changed(event)

    def _on_miniodata_storage_attached(self,event:StorageAttachedEvent):
        """Handle to action attach event"""
        # send attaching storage status 
        self.unit.status = ActiveStatus("Attaching Storage")
        # get storage name,id and location 
        self.storage_name = self.model.storages.request()
        logging.debug("storage names %s",self.storage_name)

        self._mount(self.storage_name,'/srv','ext4','rw')
        self.unit.status = ActiveStatus("Attaching Storage")

        #juju attach-stoage name data 

    def _on_config_changed(self,event):
        """Handle to config change event"""
        # Get the MinIO container so we can configure it 
        container = self.unit.get_container("minio")
        self.unit.status = ActiveStatus(str(container))
        # Create a new config layer
        layer = self._minio_cluster_layer()
        # get the current plan 
        plan = container.get_plan()
        # check if ther are any changes in service
        if plan.services != layer['services']:
        #    # Changes were made , add the new layer
            container.add_layer('minio',layer,combine=True)
            logging.info("Added updated layer 'minio' to pabble plan")
        #    # stop the service if it is already running
            if container.get_service('minio').is_running():
                container.stop('minio')
        #    # Restart it and report a new status to juju 
            container.start('minio')
            logging.info("Restarted MinIO Service")
        # All is well, set and ActiveStatus
        self.unit.status = ActiveStatus()

    def _mount(self,source,target,fs,options=''):
        ret = libc.mount(source, target, fs, 0, options)
        if ret < 0:
            errno = ctypes.get_errno()
            raise OSError(errno, "Error mounting {} ({}) on {} with options {} : {} ".format(source, fs, target, options, os.strerror(errno)))

    def on_pebble_ready(self,event):
        """Handle to pebble ready event"""
        # create new confige layer 
        layer = self._minio_cluster_layer()
        self.unit.status = ActiveStatus(str(layer))
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Add intial Pebble config layer using the Pebble API
        container.add_layer("minio",layer,combine=True)
        # Autostart any services that were defined with startup: enabled
        container.stop("minio")
        container.autostart()
        self.unit.status = ActiveStatus("Minio Layer Created")
    
    def _minio_cluster_layer(self):
        self.unit.status = ActiveStatus("Minio Layer Created")
        # self.unit.status = ActiveStatus(str(self.config['console']))

        if len(self.minio_list) < 4 :
            self.unit.status = ActiveStatus(str(len(self.minio_list)))
            return self._minio_layer()

        

        self.host = "http://minio-{0...3}"

        self.unit.status = ActiveStatus(str(self.host))
        secret_key = self.model.config["secret-key"] or self._stored.secret_key
        layer = {
            "summary": "minio layer",
            "description": "pebble config layer for minio browser",
            "services": {
                "minio": {
                    "override": "replace",
                    "summary": "minio",
                    "command": 'minio server --address :{}  --console-address ":{}" {}'.format(self.config['ports'],self.config['console'],self.host),
                    "startup": "enabled",
                    "environment": {
                        "MINIO_ACCESS_KEY": self.config["access-key"],
                        "MINIO_SECRET_KEY": secret_key,
                        "VOLUME": '/srv',
                    },
                }
            },
        }
        return layer

    def _minio_layer(self):
        """Return a Pebble confoguration layer for pabble"""
        self.unit.status = ActiveStatus("Minio Layer Created")
        self.unit.status = ActiveStatus(str(self.config['console']))

        # get the secret key 
        secret_key = self.model.config["secret-key"] or self._stored.secret_key
        layer = {
            "summary": "minio layer",
            "description": "pebble config layer for minio browser",
            "services": {
                "minio": {
                    "override": "replace",
                    "summary": "minio",
                    "command": 'minio server --address :{}  --console-address ":{}" /srv'.format(self.config['ports'],self.config['console']),
                    "startup": "enabled",
                    "environment": {
                        "MINIO_ACCESS_KEY": self.config["access-key"],
                        "MINIO_SECRET_KEY": secret_key,
                        "VOLUME": '/srv',
                    },
                }
            },
        }
        return layer

if __name__ == "__main__":
    main(MinioCharm)