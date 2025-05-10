const EParameter = struct {
    type: EType,
    required: bool = false,
    default: ?EObject = null,
};

const EParameters = struct {
    parameters: []const EParameter,
};

const EArgument = struct {
    value: EObject,
    evaluates: bool = false,
};

const EArguments = struct {
    allocator: std.mem.Allocator,
    arguments: std.StringHashMap(EArgument),

    fn init(allocator: std.mem.Allocator) EArgument {
        return .{
            .allocator = allocator,
            .arguments = std.StringHashMap(EArgument).init(allocator),
        };
    }
};

const EAttributeManager = struct {
    arguments: EArguments,
    parameters: EParameters,
};

const std = @import("std");
const objects = @import("objects.zig");
const EObject = objects.EObject;
const EType = objects.EType;
