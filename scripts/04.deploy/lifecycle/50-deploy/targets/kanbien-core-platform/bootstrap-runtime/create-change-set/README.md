# Create Core Runtime Change Set

This command has one permitted effect: create the initial CloudFormation change
set for `kanbien-core-platform-bootstrap-runtime`. It obtains every runtime
parameter from the fixed foundation outputs and the qualified custody receipt.
It never accepts a target, region, stack, image, or source-revision selector.

The change set is an intermediate review artifact. Creating it is not
deployment; a separate execution control must validate its exact changes and
receive mutation authority before it can run.
