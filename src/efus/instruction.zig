pub const InstantiateComponent = struct {
    componentName: []const u8,
    componentAlias: ?[]const u8,
    children: []Instruction,
    arguments: std.StringHashMap(InstantiateComponentArgument),
    allocator: std.mem.Allocator,

    pub fn evaluate(self: *Instruction, names: namespace.Namespace, _: ?Instruction) !EObject {
        var value: ?EObject = null;
        for (self.children) |child| {
            value = child.evaluate(names, self);
        }
        return value;
    }
    pub fn init(
        allocator: std.mem.Allocator,
        name: []const u8,
        alias: ?[]const u8,
        args: ?std.StringHashMap(InstantiateComponentArgument),
    ) InstantiateComponent {
        return .{
            .componentName = name,
            .componentAlias = alias,
            .children = &[_]Instruction{},
            .arguments = args orelse std.StringHashMap(InstantiateComponentArgument).init(allocator),
            .allocator = allocator,
        };
    }
};
pub const Instruction = union(enum) {
    InstantiateComponent: InstantiateComponent,
};

pub const InstantiateComponentArgument = struct {
    key: []const u8,
    value: EObject,
};

const std = @import("std");
const objects = @import("objects.zig");
const EObject = objects.EObject;
const namespace = @import("namespace.zig");
