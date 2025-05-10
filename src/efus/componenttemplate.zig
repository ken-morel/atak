pub const ComponentTemplate = struct {
    name: []const u8,
    renderer: backend.RendererBackend,
    parameters: attributemanager.EParameters,
};

const objs = @import("objects");
const std = @import("std");
const backend = @import("backend.zig");
const attributemanager = @import("attributemanager.zig");
