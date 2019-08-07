from rest_framework import serializers
from goods.models import Goods
from trade.models import ShoppingCart, OrderInfo, OrderGoods
from goods.serializers import GoodsSerializer


class ShoppingCartListSerializer(serializers.ModelSerializer):
    goods = GoodsSerializer(many=False)  # 一个购物车的记录只会对应一个商品，默认many=False，也就是可以不写

    class Meta:
        model = ShoppingCart
        fields = "__all__"


class ShoppingCartSerializer(serializers.Serializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()  # 表示user为隐藏字段，默认为获取当前登录用户
    )
    nums = serializers.IntegerField(required=True, min_value=1, label='商品数量', help_text='商品数量',
                                    error_messages={
                                        'min_value': '商品数量不能小于1',
                                        'required': '请选择购买数量'
                                    })
    goods = serializers.PrimaryKeyRelatedField(queryset=Goods.objects.all(), required=True, label='商品')

    def create(self, validated_data):
        user = self.context['request'].user  # serializer中获取当前用户，而views是直接从request中获取
        nums = validated_data['nums']
        goods = validated_data['goods']

        # 查询记录是否存在，存在，则进行数量加，不存在则新创建
        shopping_cart = ShoppingCart.objects.filter(user=user, goods=goods)
        if shopping_cart:
            shopping_cart = shopping_cart.first()
            shopping_cart.nums += nums
            shopping_cart.save()
        else:
            shopping_cart = ShoppingCart.objects.create(**validated_data)
        # 最后要返回创建后的结果
        return shopping_cart

    def update(self, instance, validated_data):
        instance.nums = validated_data['nums']  # 从validated_data中获取商品数量去更新购物车
        instance.save()
        return instance


class OrderInfoSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()  # 表示user为隐藏字段，默认为获取当前登录用户
    )
    order_sn = serializers.CharField(read_only=True)  # 只能读，不能显示给用户修改，只能后台去修改
    trade_no = serializers.CharField(read_only=True)  # 只读
    pay_status = serializers.CharField(read_only=True)  # 只读
    pay_time = serializers.DateTimeField(read_only=True)  # 只读

    def generate_order_sn(self):
        # 当前时间+userid+随机数
        import time
        from random import randint
        order_sn = '{time_str}{user_id}{random_str}'.format(time_str=time.strftime('%Y%m%d%H%M%S'), user_id=self.context['request'].user.id, random_str=randint(10, 99))
        return order_sn

    def validate(self, attrs):
        # 数据验证成功后，生成一个订单号
        attrs['order_sn'] = self.generate_order_sn()
        return attrs

    class Meta:
        model = OrderInfo
        fields = "__all__"


# 订单中的商品序列化
class OrderGoodsSerializer(serializers.ModelSerializer):
    goods = GoodsSerializer()  # 直接用goods.serializers商品详情的序列化

    class Meta:
        model = OrderGoods
        fields = "__all__"


# 订单详情序列化
class OrderInfoDetailSerializer(serializers.ModelSerializer):
    order_goods = OrderGoodsSerializer(many=True)  # 为OrderGoods中外键关联名称

    class Meta:
        model = OrderInfo
        fields = "__all__"
