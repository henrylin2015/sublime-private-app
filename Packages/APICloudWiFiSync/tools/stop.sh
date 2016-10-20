#!/bin/bash
Name='wifisync.jar'
pid=`ps -ef | grep $Name | grep -v "grep" | awk '{print $2}'`
kill $pid
