pub const ComponentTemplate = struct {
    name: []const u8,
    renderer: backend.RendererBackend,
    parameters: attributemanager.EParameters,

    pub fn instantiate(
        self: ComponentTemplate,
        allocator: std.mem.Allocator,
        namespace: Namespace,
        args: attributemanager.EArguments,
        master: ?component.Component,
    ) !component.Component {
        var comp = try component.Component.init(
            allocator,
            self,
            namespace,
            args,
        );
        try self.renderer.init(&comp, master);
        return comp;
    }
};

const std = @import("std");
const backend = @import("backend.zig");
const attributemanager = @import("attributemanager.zig");
const component = @import("component.zig");
const Namespace = @import("namespace.zig").Namespace;
