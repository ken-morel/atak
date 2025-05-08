const Instruction = union(enum) {
    Tagdef: struct {
        tagName: []const u8,
        tagAlias: ?[]const u8,
        children: []const Instruction,
        attributes: std.ArrayListUnmanaged(Attribute),
    },
};

const Attribute = struct {
    key: []const u8,
    value: objects.Value,
};

const std = @import("std");
const objects = @import("objects.zig");
