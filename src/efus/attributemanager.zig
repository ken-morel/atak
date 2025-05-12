pub const EParameter = struct {
    name: []const u8,
    type: EType,
    required: bool = false,
    default: ?EObject = null,
};

pub const EParameters = struct {
    parameters: []const EParameter,
};

pub const EArgument = struct {
    value: EObject,
    evaluates: bool = false,
    pub fn eval(self: *EArgument, _: Namespace) !EObject {
        return self.value;
    }
};

pub const EArguments = struct {
    allocator: std.mem.Allocator,
    arguments: std.StringHashMap(EArgument),

    pub fn init(allocator: std.mem.Allocator) EArguments {
        return .{
            .allocator = allocator,
            .arguments = std.StringHashMap(EArgument).init(allocator),
        };
    }
    pub fn fromICArgs(
        allocator: std.mem.Allocator,
        args: std.ArrayList(InstantiateComponentArgument),
    ) !EArguments {
        var arguments = std.StringHashMap(EArgument).init(allocator);
        for (args.items) |argument| {
            try arguments.put(argument.key, EArgument{
                .value = argument.value,
                .evaluates = false,
            });
        }
        return .{
            .allocator = allocator,
            .arguments = arguments,
        };
    }

    pub fn put(self: *EArguments, key: []const u8, arg: EArgument) !void {
        try self.arguments.put(key, arg);
    }
};

pub const EAttribute = struct {
    parameter: EParameter,
    argument: EArgument,
    pub fn init(parameter: EParameter, argument: EArgument) EAttribute {
        return EAttribute{
            .parameter = parameter,
            .argument = argument,
        };
    }
    pub fn typeCheck(self: *EAttribute) !void {
        if (!self.argument.value.isType(self.parameter.type)) {
            return EfusError.ArgumentTypeError;
        }
    }
    pub fn eval(self: *EAttribute, names: Namespace) !EObject {
        return self.argument.eval(names);
    }
};
pub const EAttributeManager = struct {
    arguments: EArguments,
    parameters: EParameters,
    attributes: std.StringHashMap(EAttribute),

    pub fn init(allocator: std.mem.Allocator, params: EParameters, args: EArguments) !EAttributeManager {
        var attributes = std.StringHashMap(EAttribute).init(allocator);
        errdefer attributes.deinit();

        var used_keys = std.StringHashMap(void).init(allocator);
        defer used_keys.deinit();

        for (params.parameters) |param| {
            const param_name = param.name;

            if (args.arguments.get(param_name)) |arg| {
                const attribute = EAttribute.init(param, arg);
                try attributes.put(param_name, attribute);
                try used_keys.put(param_name, {});
            } else if (param.default) |default_val| {
                const default_arg = EArgument{
                    .value = default_val,
                    .evaluates = false,
                };
                const attribute = EAttribute.init(param, default_arg);
                try attributes.put(param_name, attribute);
            } else if (param.required) {
                return EfusError.MissingRequiredArgument;
            }
        }

        var it = args.arguments.iterator();
        while (it.next()) |entry| {
            if (!used_keys.contains(entry.key_ptr.*)) {
                return EfusError.UnexpectedArgument;
            }
        }

        return EAttributeManager{
            .arguments = args,
            .parameters = params,
            .attributes = attributes,
        };
    }
};

const std = @import("std");
const objects = @import("objects.zig");
const EObject = objects.EObject;
const EType = objects.EType;
const InstantiateComponentArgument = @import("instruction.zig").InstantiateComponentArgument;
const EfusError = @import("errors.zig").EfusError;
const Namespace = @import("namespace.zig").Namespace;
