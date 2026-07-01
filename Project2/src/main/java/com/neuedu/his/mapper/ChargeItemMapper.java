package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.ChargeItem;
import com.neuedu.his.model.vo.ChargeItemVO;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@Mapper
public interface ChargeItemMapper {

    @Insert("INSERT INTO charge_item(source_id, source_type, register_id, item_name, item_type, amount, status, create_time, update_time) " +
            "VALUES(#{sourceId}, #{sourceType}, #{registerId}, #{itemName}, #{itemType}, #{amount}, #{status}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(ChargeItem chargeItem);

    @Select("SELECT * FROM charge_item WHERE register_id = #{registerId} AND status = 'PENDING'")
    List<ChargeItem> selectPendingByRegisterId(Integer registerId);

    @Select("SELECT * FROM charge_item WHERE register_id = #{registerId} AND status = 'CHARGED'")
    List<ChargeItem> selectChargedByRegisterId(Integer registerId);

    @Select("<script>SELECT * FROM charge_item WHERE id IN " +
            "<foreach collection='ids' item='id' open='(' separator=',' close=')'>#{id}</foreach> " +
            "AND status = 'PENDING'</script>")
    List<ChargeItem> selectPendingByIds(@Param("ids") List<Long> ids);

    @Select("<script>SELECT * FROM charge_item WHERE id IN " +
            "<foreach collection='ids' item='id' open='(' separator=',' close=')'>#{id}</foreach> " +
            "AND status = 'CHARGED'</script>")
    List<ChargeItem> selectChargedByIds(@Param("ids") List<Long> ids);

    @Update("UPDATE charge_item SET status = 'CHARGED', finance_record_id = #{financeRecordId}, " +
            "charge_method = #{chargeMethod}, charge_time = CURRENT_TIMESTAMP, operator_id = #{operatorId}, update_time = CURRENT_TIMESTAMP " +
            "WHERE id = #{id}")
    int charge(@Param("id") Long id,
               @Param("financeRecordId") Long financeRecordId,
               @Param("chargeMethod") String chargeMethod,
               @Param("operatorId") Integer operatorId);

    @Update("UPDATE charge_item SET status = 'REFUNDED', refund_reason = #{refundReason}, refund_time = CURRENT_TIMESTAMP, update_time = CURRENT_TIMESTAMP " +
            "WHERE id = #{id}")
    int refund(@Param("id") Long id, @Param("refundReason") String refundReason);

    List<ChargeItemVO> selectRecords(@Param("startDate") LocalDate startDate,
                                     @Param("endDate") LocalDate endDate,
                                     @Param("chargeMethod") String chargeMethod,
                                     @Param("status") String status);

    Map<String, Object> selectDailySummary(@Param("summaryDate") LocalDate summaryDate);

    @Select("SELECT * FROM charge_item WHERE source_id = #{sourceId} AND source_type = #{sourceType}")
    ChargeItem selectBySource(@Param("sourceId") Integer sourceId, @Param("sourceType") String sourceType);
}
