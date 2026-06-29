package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.FinanceRecord;
import com.neuedu.his.model.vo.FinanceRecordVO;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface FinanceRecordMapper {

    @Insert("INSERT INTO finance_record(record_no, register_id, item_id, item_type, item_name, amount, charge_method, record_type, operator_name) " +
            "VALUES(#{recordNo}, #{registerId}, #{itemId}, #{itemType}, #{itemName}, #{amount}, #{chargeMethod}, #{recordType}, #{operatorName})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(FinanceRecord record);

    @Select("""
            <script>
            SELECT fr.id,
                   fr.record_no,
                   fr.register_id,
                   COALESCE(p.real_name, '未知患者') AS patient_name,
                   fr.item_type,
                   fr.item_name,
                   fr.amount,
                   fr.charge_method,
                   fr.record_type,
                   fr.create_time,
                   fr.operator_name
            FROM finance_record fr
                     LEFT JOIN register r ON fr.register_id = r.id
                     LEFT JOIN patient p ON r.patient_id = p.id
            WHERE 1 = 1
              <if test="startTime != null">AND fr.create_time &gt;= #{startTime}</if>
              <if test="endTimeExclusive != null">AND fr.create_time &lt; #{endTimeExclusive}</if>
              <if test="chargeMethod != null and chargeMethod != ''">AND fr.charge_method = #{chargeMethod}</if>
              <if test="recordType != null and recordType != ''">AND fr.record_type = #{recordType}</if>
            ORDER BY fr.create_time DESC, fr.id DESC
            </script>
            """)
    List<FinanceRecordVO> selectByCondition(@Param("startTime") LocalDateTime startTime,
                                            @Param("endTimeExclusive") LocalDateTime endTimeExclusive,
                                            @Param("chargeMethod") String chargeMethod,
                                            @Param("recordType") String recordType);
}
