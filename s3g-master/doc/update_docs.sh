#!/bin/sh

# Build the documents. Requires that GraphViz be installed.

dot PacketStreamDecoder.dot -Tpng > PacketStreamDecoder.png
dot send_command.dot -Tpng > send_command.png
dot check_response_code.dot -Tpng > check_response_code.png
dot GCodeStateMachine.dot -Tpng > GCodeStateMachine.png
dot MCodeStateMachine.dot -Tpng > MCodeStateMachine.png
dot s3gErrors.dot -Tpng > s3gErrors.png
dot CurrentErrors.dot -Tpng > CurrentErrors.png

mscgen -i HostCommandSuccess.msc -T png
mscgen -i ToolCommandSuccess.msc -T png
mscgen -i HostToolCommandSuccess.msc -T png

