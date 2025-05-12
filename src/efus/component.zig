pub const Component = struct {
    allocator: std.mem.Allocator,
    args: attributemanager.EAttributeManager,
    template: componenttemplate.ComponentTemplate,
    namespace: Namespace,
    _mount: ?backend.Mount = null,
    dirty: bool = false,
    children: std.ArrayList(Component),

    pub fn mount(self: *Component) anyerror!void {
        try self.template.renderer.mount(self);
    }
    pub fn update(self: *Component) anyerror!void {
        try self.template.renderer.update(self);
    }
    pub fn unmount(self: *Component) anyerror!void {
        try self.template.renderer.unmount(self);
    }

    pub fn init(
        allocator: std.mem.Allocator,
        template: componenttemplate.ComponentTemplate,
        namespace: Namespace,
        args: attributemanager.EArguments,
    ) !Component {
        return Component{
            .allocator = allocator,
            .args = try attributemanager.EAttributeManager.init(
                allocator,
                template.parameters,
                args,
            ),
            .template = template,
            .namespace = namespace,
            .children = std.ArrayList(Component).init(allocator),
        };
    }

    pub fn addChild(self: *Component, child: Component) !void {
        std.debug.print("Added child", .{});
        try self.children.append(child);
    }
};

const std = @import("std");
const attributemanager = @import("attributemanager.zig");
const backend = @import("backend.zig");
const Namespace = @import("namespace.zig").Namespace;
const componenttemplate = @import("componenttemplate.zig");
